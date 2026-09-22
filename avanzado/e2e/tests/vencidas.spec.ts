import { test, expect, type APIRequestContext, type Locator, type Page } from '@playwright/test';

/**
 * Criterio de `specs/prioridad-y-fecha-limite.md` (Página web):
 *
 *   "Las tareas vencidas se ven distintas de las no vencidas; una tarea
 *    completada con fecha pasada no se marca como vencida."
 *
 * `tests/test_web.py` ya cubre el markup: comprueba que el `<li>` de una tarea
 * vencida sale con `class="overdue"`. Eso verifica que el servidor decide bien
 * quién está vencida, pero no que se vea algo: la clase puede quedar sin ninguna
 * regla CSS y el HTML sigue siendo idéntico.
 *
 * Por eso acá no miramos clases ni texto, sino los estilos computados que el
 * navegador aplica de verdad a la fila.
 */

/** Fecha local en `YYYY-MM-DD`, desplazada `dias` respecto de hoy. */
function fechaRelativa(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() + dias);
  const mes = String(d.getMonth() + 1).padStart(2, '0');
  const dia = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mes}-${dia}`;
}

/**
 * Cómo se ve la fila: lo que distingue a una tarea vencida del resto es el
 * tratamiento del `<li>` (fondo, borde, sangría) y el de su fecha límite.
 * No fijamos colores concretos a propósito — el criterio pide que se vean
 * distintas, no que sean de un rojo en particular.
 */
type FirmaVisual = {
  fondo: string;
  borde: string;
  sangria: string;
  colorFecha: string | null;
  pesoFecha: string | null;
};

async function firmaVisual(fila: Locator): Promise<FirmaVisual> {
  return fila.evaluate((li: HTMLElement): FirmaVisual => {
    const s = getComputedStyle(li);
    const fecha = li.querySelector('.due');
    const f = fecha ? getComputedStyle(fecha) : null;
    return {
      fondo: s.backgroundColor,
      borde: `${s.borderLeftWidth} ${s.borderLeftStyle} ${s.borderLeftColor}`,
      sangria: s.paddingLeft,
      colorFecha: f ? f.color : null,
      pesoFecha: f ? f.fontWeight : null,
    };
  });
}

/** La fila de una tarea, ubicada por id y no por texto, para no depender del título. */
function fila(page: Page, id: number): Locator {
  return page.locator(`li:has(form[action="/ui/tasks/${id}/delete"])`);
}

async function crearTarea(
  api: APIRequestContext,
  datos: { title: string; due_date: string | null },
): Promise<number> {
  const res = await api.post('/tasks', { data: { priority: 'media', ...datos } });
  expect(res.status(), `no se pudo crear la tarea "${datos.title}"`).toBe(201);
  return (await res.json()).id;
}

// Las fechas se calculan respecto de hoy, así que el test vale cualquier día
// en que se corra; las tareas se crean y se borran acá mismo para no depender
// del seed ni dejar basura en `tasks.db`.
let idVencida: number;
let idAlDia: number;
let idCompletadaConFechaPasada: number;

test.beforeAll(async ({ playwright, baseURL }) => {
  const api = await playwright.request.newContext({ baseURL });
  idVencida = await crearTarea(api, { title: 'E2E vencida', due_date: fechaRelativa(-7) });
  idAlDia = await crearTarea(api, { title: 'E2E al dia', due_date: fechaRelativa(7) });
  idCompletadaConFechaPasada = await crearTarea(api, {
    title: 'E2E completada con fecha pasada',
    due_date: fechaRelativa(-7),
  });
  const completar = await api.patch(`/tasks/${idCompletadaConFechaPasada}/complete`);
  expect(completar.status()).toBe(200);
  await api.dispose();
});

test.afterAll(async ({ playwright, baseURL }) => {
  const api = await playwright.request.newContext({ baseURL });
  for (const id of [idVencida, idAlDia, idCompletadaConFechaPasada]) {
    await api.delete(`/tasks/${id}`);
  }
  await api.dispose();
});

test.beforeEach(async ({ page }) => {
  await page.goto('/');
});

test('la tarea vencida se ve distinta de la que todavía no venció', async ({ page }) => {
  await expect(fila(page, idVencida)).toBeVisible();

  const vencida = await firmaVisual(fila(page, idVencida));
  const alDia = await firmaVisual(fila(page, idAlDia));

  expect(
    vencida,
    'la tarea vencida se renderiza igual que una no vencida: el navegador no le ' +
      'aplica ningún estilo propio (fondo, borde, sangría ni color de fecha)',
  ).not.toEqual(alDia);
});

test('la marca "Vencida" se destaca del resto de la línea de datos', async ({ page }) => {
  const marca = fila(page, idVencida).locator('.overdue-label');
  await expect(marca).toBeVisible();

  const { colorMarca, colorAlrededor, pesoMarca, pesoAlrededor } = await fila(page, idVencida).evaluate(
    (li: HTMLElement) => {
      const etiqueta = li.querySelector('.overdue-label') as HTMLElement;
      const meta = li.querySelector('.meta') as HTMLElement;
      return {
        colorMarca: getComputedStyle(etiqueta).color,
        colorAlrededor: getComputedStyle(meta).color,
        pesoMarca: getComputedStyle(etiqueta).fontWeight,
        pesoAlrededor: getComputedStyle(meta).fontWeight,
      };
    },
  );

  expect(
    `${colorMarca} / ${pesoMarca}`,
    'la palabra "Vencida" se ve igual que el resto del texto de la fila: está en ' +
      'el HTML pero sin ningún resalte visual',
  ).not.toEqual(`${colorAlrededor} / ${pesoAlrededor}`);
});

test('una tarea completada con fecha pasada no se destaca como vencida', async ({ page }) => {
  const completada = await firmaVisual(fila(page, idCompletadaConFechaPasada));
  const alDia = await firmaVisual(fila(page, idAlDia));

  expect(
    { fondo: completada.fondo, borde: completada.borde, sangria: completada.sangria },
    'una tarea completada con fecha pasada quedó resaltada como vencida',
  ).toEqual({ fondo: alDia.fondo, borde: alDia.borde, sangria: alDia.sangria });

  await expect(fila(page, idCompletadaConFechaPasada).locator('.overdue-label')).toHaveCount(0);
});
