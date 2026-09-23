import { test, expect, type Page, type APIRequestContext } from '@playwright/test';

/**
 * Criterios de `specs/prioridad-y-fecha-limite.md` (sección "Página web"):
 *
 *   - "Aplicar los controles navega a `/` con los query params `priority`,
 *      `completed`, `overdue` y `sort_by`, y el listado muestra el mismo
 *      resultado que `GET /tasks` con esos parámetros."
 *   - "Si hay tareas pero ninguna coincide con los filtros, la página muestra
 *      un mensaje que lo indica."
 *
 * Los filtros se combinan entre sí, así que lo que hay que comprobar no es cada
 * uno por separado sino que la combinación de los tres deja en el listado solo
 * lo que cumple las tres condiciones. Estos tests operan los controles de
 * verdad (selects, checkbox, botón Aplicar) y miran cómo queda el listado.
 */

/** Fecha local en `YYYY-MM-DD`, corrida `dias` días. */
function fecha(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() + dias);
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mes}-${dia}`;
}

// Cuatro tareas armadas alrededor de la combinación `alta` + `pendiente` +
// `vencida`: una que la cumple entera y tres que fallan en una sola condición.
// Así un filtro que se ignore, o que se aplique de más, se nota enseguida.
const TAREAS = {
  cumpleTodo: { titulo: 'E2E alta pendiente vencida', priority: 'alta', due: fecha(-1), completar: false },
  noVencida: { titulo: 'E2E alta pendiente futura', priority: 'alta', due: fecha(+7), completar: false },
  otraPrioridad: { titulo: 'E2E media pendiente vencida', priority: 'media', due: fecha(-1), completar: false },
  completada: { titulo: 'E2E alta completada vencida', priority: 'alta', due: fecha(-1), completar: true },
} as const;

type Clave = keyof typeof TAREAS;
const CLAVES = Object.keys(TAREAS) as Clave[];

let sufijo = '';
let creadas: number[] = [];

/** Título único de esta corrida, para no chocar con lo que ya haya en la base. */
function titulo(clave: Clave): string {
  return `${TAREAS[clave].titulo} ${sufijo}`;
}

/** Títulos de las tareas que el listado muestra, en el orden en que se ven. */
async function titulosDelListado(page: Page): Promise<string[]> {
  return page.locator('li .title').allTextContents();
}

/** Query params no vacíos de la URL actual. */
function paramsDeLaUrl(page: Page): Record<string, string> {
  const params = new URL(page.url()).searchParams;
  return Object.fromEntries([...params].filter(([, valor]) => valor !== ''));
}

/** Los mismos filtros, pero preguntados a la API. */
async function titulosSegunLaApi(request: APIRequestContext, query: string): Promise<string[]> {
  const respuesta = await request.get(`/tasks?${query}`);
  expect(respuesta.status()).toBe(200);
  const tareas = (await respuesta.json()) as { title: string }[];
  return tareas.map((t) => t.title);
}

test.beforeEach(async ({ request }) => {
  sufijo = Math.random().toString(36).slice(2, 8);
  creadas = [];

  for (const clave of CLAVES) {
    const { priority, due, completar } = TAREAS[clave];
    const alta = await request.post('/tasks', {
      data: { title: titulo(clave), priority, due_date: due },
    });
    expect(alta.status(), `no se pudo crear la tarea "${titulo(clave)}"`).toBe(201);

    const { id } = await alta.json();
    creadas.push(id);

    if (completar) {
      expect((await request.patch(`/tasks/${id}/complete`)).status()).toBe(200);
    }
  }
});

test.afterEach(async ({ request }) => {
  for (const id of creadas) {
    await request.delete(`/tasks/${id}`);
  }
});

test.describe('Criterio: el listado se actualiza según la combinación de filtros', () => {
  test('prioridad + estado + solo vencidas deja solo lo que cumple las tres', async ({ page, request }) => {
    await page.goto('/');

    // Sin filtros, las cuatro tareas de la prueba están en el listado.
    const sinFiltros = await titulosDelListado(page);
    for (const clave of CLAVES) {
      expect(sinFiltros, `"${titulo(clave)}" debería verse sin filtros`).toContain(titulo(clave));
    }

    await page.getByLabel('Filtrar por prioridad').selectOption('alta');
    await page.getByLabel('Filtrar por estado').selectOption('false');
    await page.getByLabel('Solo vencidas').check();
    await page.getByRole('button', { name: 'Aplicar' }).click();

    expect(paramsDeLaUrl(page)).toMatchObject({
      priority: 'alta',
      completed: 'false',
      overdue: 'true',
    });

    // De las cuatro, solo sobrevive la que cumple las tres condiciones.
    const filtrado = await titulosDelListado(page);
    expect(filtrado).toContain(titulo('cumpleTodo'));
    for (const clave of ['noVencida', 'otraPrioridad', 'completada'] as Clave[]) {
      expect(filtrado, `"${titulo(clave)}" no debería pasar el filtro`).not.toContain(titulo(clave));
    }

    // Y el listado completo coincide con lo que devuelve la API con esos params.
    expect(filtrado).toEqual(
      await titulosSegunLaApi(request, 'priority=alta&completed=false&overdue=true'),
    );

    // Los controles quedan reflejando los filtros aplicados.
    await expect(page.getByLabel('Filtrar por prioridad')).toHaveValue('alta');
    await expect(page.getByLabel('Filtrar por estado')).toHaveValue('false');
    await expect(page.getByLabel('Solo vencidas')).toBeChecked();
  });

  test('cambiar la combinación vuelve a actualizar el listado', async ({ page, request }) => {
    await page.goto('/?priority=alta&completed=false&overdue=true');
    expect(await titulosDelListado(page)).not.toContain(titulo('noVencida'));

    // Se afloja una sola condición: se destilda "Solo vencidas".
    await page.getByLabel('Solo vencidas').uncheck();
    await page.getByRole('button', { name: 'Aplicar' }).click();

    expect(paramsDeLaUrl(page)).toMatchObject({ priority: 'alta', completed: 'false' });
    expect(paramsDeLaUrl(page)).not.toHaveProperty('overdue');

    // Ahora entra la de fecha futura; las otras dos siguen afuera.
    const filtrado = await titulosDelListado(page);
    expect(filtrado).toContain(titulo('cumpleTodo'));
    expect(filtrado).toContain(titulo('noVencida'));
    expect(filtrado).not.toContain(titulo('otraPrioridad'));
    expect(filtrado).not.toContain(titulo('completada'));

    expect(filtrado).toEqual(await titulosSegunLaApi(request, 'priority=alta&completed=false'));
  });

  test('una combinación sin coincidencias muestra el mensaje de sin resultados', async ({ page }) => {
    await page.goto('/');

    // "Completadas" + "Solo vencidas" no puede dar resultados: por definición,
    // una tarea completada nunca está vencida.
    await page.getByLabel('Filtrar por estado').selectOption('true');
    await page.getByLabel('Solo vencidas').check();
    await page.getByRole('button', { name: 'Aplicar' }).click();

    expect(paramsDeLaUrl(page)).toMatchObject({ completed: 'true', overdue: 'true' });

    await expect(page.getByRole('listitem')).toHaveCount(0);
    await expect(page.locator('.empty')).toHaveText('Ninguna tarea coincide con los filtros.');
  });
});
