import { test, expect, type Locator, type APIRequestContext } from '@playwright/test';

/**
 * Criterio de `specs/prioridad-y-fecha-limite.md`:
 *
 *   "Las tareas vencidas se ven distintas de las no vencidas; una tarea
 *    completada con fecha pasada no se marca como vencida."
 *
 * `tests/test_web.py` lo da por cubierto mirando el HTML (`<li class="overdue">`).
 * Eso verifica que el backend clasifica bien, no que la tarea *se vea* distinta:
 * si la regla CSS `li.overdue` desaparece, el HTML sigue igual y el test de
 * pytest sigue pasando, pero en el navegador las dos filas son idénticas.
 *
 * Estos tests abren la página de verdad y comparan los estilos calculados que
 * el navegador termina aplicando a cada fila.
 */

// Propiedades con las que una fila puede verse distinta de otra. Se compara el
// `<li>` completo (el contenedor de la tarea), que es donde vive el destaque de
// vencida. Es un conjunto amplio a propósito: sirve igual si el destaque se
// hace con fondo, con borde, con color de texto o atenuando la fila.
const ESTILOS_DE_FILA = [
  'background-color',
  'border-left-width',
  'border-left-style',
  'border-left-color',
  'color',
  'font-weight',
  'text-decoration-line',
  'opacity',
];

type Fila = Record<string, string>;

/** Fecha local del navegador/servidor en `YYYY-MM-DD`, corrida `dias` días. */
function fecha(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() + dias);
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mes}-${dia}`;
}

/** Estilos que el navegador aplica realmente a la fila de una tarea. */
async function estilosDeFila(fila: Locator): Promise<Fila> {
  return fila.evaluate((li, props: string[]) => {
    const calculado = getComputedStyle(li as Element);
    return Object.fromEntries(props.map((p) => [p, calculado.getPropertyValue(p)]));
  }, ESTILOS_DE_FILA);
}

// Tareas creadas por API con fechas relativas a hoy, para que los tests pasen
// cualquier día que se corran (criterio de la spec) y no dependan del seed.
const TAREAS = {
  vencida: { titulo: 'E2E vencida', due_date: fecha(-1), completar: false },
  futura: { titulo: 'E2E futura', due_date: fecha(+7), completar: false },
  completadaVencida: { titulo: 'E2E completada con fecha pasada', due_date: fecha(-1), completar: true },
};

let sufijo = '';
let creadas: number[] = [];

/** Título único de esta corrida, para no chocar con lo que ya haya en la base. */
function titulo(tarea: keyof typeof TAREAS): string {
  return `${TAREAS[tarea].titulo} ${sufijo}`;
}

/** La fila del listado correspondiente a una de las tareas creadas. */
function fila(page: import('@playwright/test').Page, tarea: keyof typeof TAREAS): Locator {
  return page.getByRole('listitem').filter({ hasText: titulo(tarea) });
}

test.beforeEach(async ({ request }: { request: APIRequestContext }) => {
  sufijo = Math.random().toString(36).slice(2, 8);
  creadas = [];

  for (const clave of Object.keys(TAREAS) as (keyof typeof TAREAS)[]) {
    const { due_date, completar } = TAREAS[clave];
    const alta = await request.post('/tasks', {
      data: { title: titulo(clave), priority: 'media', due_date },
    });
    expect(alta.status(), `no se pudo crear la tarea "${titulo(clave)}"`).toBe(201);

    const { id } = await alta.json();
    creadas.push(id);

    if (completar) {
      const completada = await request.patch(`/tasks/${id}/complete`);
      expect(completada.status()).toBe(200);
    }
  }
});

test.afterEach(async ({ request }: { request: APIRequestContext }) => {
  for (const id of creadas) {
    await request.delete(`/tasks/${id}`);
  }
});

test.describe('Criterio: las tareas vencidas se ven distintas de las no vencidas', () => {
  test('la tarea vencida se destaca visualmente frente a una no vencida', async ({ page }) => {
    await page.goto('/');

    const vencida = fila(page, 'vencida');
    const futura = fila(page, 'futura');
    await expect(vencida).toBeVisible();
    await expect(futura).toBeVisible();

    const [estiloVencida, estiloFutura] = await Promise.all([
      estilosDeFila(vencida),
      estilosDeFila(futura),
    ]);

    // El HTML puede marcar la tarea como vencida (class="overdue") y aun así
    // renderizarse idéntica si no hay CSS que la acompañe: eso es lo que este
    // test tiene que detectar.
    expect(
      estiloVencida,
      'la fila vencida y la no vencida se renderizan con los mismos estilos: ' +
        'en el navegador no se distinguen',
    ).not.toEqual(estiloFutura);
  });

  test('la tarea vencida muestra su marca de vencida y la no vencida no', async ({ page }) => {
    await page.goto('/');

    await expect(fila(page, 'vencida')).toContainText('Vencida');
    await expect(fila(page, 'futura')).not.toContainText('Vencida');
  });

  test('una tarea completada con fecha pasada no se ve como vencida', async ({ page }) => {
    await page.goto('/');

    const completada = fila(page, 'completadaVencida');
    await expect(completada).toBeVisible();
    await expect(completada).not.toContainText('Vencida');

    const [estiloCompletada, estiloFutura] = await Promise.all([
      estilosDeFila(completada),
      estilosDeFila(fila(page, 'futura')),
    ]);

    // La fila completada tiene su propio tratamiento (el título tachado), pero
    // el contenedor no debe llevar el destaque de vencida.
    expect(
      estiloCompletada,
      'la tarea completada con fecha pasada se está destacando como vencida',
    ).toEqual(estiloFutura);
  });
});
