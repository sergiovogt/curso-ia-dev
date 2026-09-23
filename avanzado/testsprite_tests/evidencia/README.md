# Evidencia de las corridas de TestSprite

Nivel `avanzado/`, página server-rendered en `http://localhost:8010`.
Fecha: 2026-09-22. Plan usado: `testsprite_frontend_test_plan.json` (19 casos, generado
a partir del `code_summary.yaml` frontend).

## Estado de la base al momento de correr

Base `tasks.db` en su estado sembrado, sin modificar. "Hoy" = 2026-09-22.

| id | título | completada | vence | ¿vencida? | clase del `<li>` |
|---|---|---|---|---|---|
| 1 | Configurar el pipeline de CI | sí | 2026-06-10 | no (está completada) | `done` |
| 2 | Migrar el login a OAuth | no | 2026-07-01 | **sí** | `overdue` |
| 3 | Escribir la doc del endpoint de pagos | no | — | no (sin fecha) | *(vacía)* |
| 4 | Revisar el PR de checkout | no | 2027-12-15 | no (fecha futura) | *(vacía)* |
| 5 | Actualizar dependencias de FastAPI | sí | — | no | `done` |

Sólo la tarea 2 lleva `<span class="overdue-label">Vencida</span>`. Verificado por HTTP
directo contra la página, además de por los tests.

## Corridas

### TC013 — Mostrar solo tareas vencidas (filtro)

- Carpeta: `TC013/`
- Estado: **PASSED**
- Duración: 12:13:39 → 12:15:20 (~1m 45s)
- Qué valida: activar el checkbox "Solo vencidas", aplicar, y que quede visible
  únicamente la tarea vencida no completada, con el filtro todavía tildado.

### TC001 — Ver la lista sembrada con estados visuales

- Carpeta: `TC001/`
- Estado: **PASSED**
- Duración: 12:18:10 → 12:30:20 (~12m)
- Qué valida *según el plan*: que las tareas sembradas se muestren, que las completadas
  se vean como completadas y que las vencidas se vean resaltadas.

## Lectura crítica de TC001 — el verde no alcanza

El caso pasó, pero el código Playwright generado **no cubre la consigna** de que las
vencidas estén identificadas *respecto de las demás*. Lo que realmente asertó:

1. `li[2]/form[1]/button` tiene texto "Completar" → hay una tarea pendiente.
2. `li[1]/form/button` y `li[5]/form/button` tienen texto "Borrar" → infiere que están
   completadas por la *ausencia* del botón "Completar".
3. `li[2]/div/div[3]/span[3]` tiene texto "Vencida" → la fila 2 muestra la etiqueta.

Lo que **no** asertó, y es justamente lo discriminante:

- Que la tarea 1 (completada, con fecha límite pasada) **no** lleve la marca de vencida.
  Es el borde donde la regla `not completed and due_date < hoy` se puede romper.
- Que la tarea 4 (pendiente, con fecha futura) **no** la lleve.
- Que la tarea 3 (pendiente, sin fecha) **no** la lleve.
- Las clases CSS reales: `overdue` en el `<li>` y `done` en las completadas. La
  "completitud" la dedujo de qué botones hay, no del tachado ni de la clase.

Problemas de robustez del código generado:

- Todos los selectores son **XPath absolutos** (`/html/body/ul/li[2]/...`), atados a la
  posición en el DOM y al orden de la base sembrada. Cualquier alta o baja corre las
  filas y el test pasa a asertar sobre la tarea equivocada — o peor, sigue en verde
  asertando otra cosa.
- `span[3]` para la etiqueta "Vencida" depende de que la fila tenga también el span de
  fecha límite. Una tarea vencida sin `due_date` no existe por definición, pero el
  selector igual es frágil.
- Las líneas tienen la forma `await expect(...), "mensaje"`, que en Python es una tupla,
  no un mensaje de assert. No rompe nada porque `expect` ya levanta excepción, pero el
  texto no cumple ninguna función.

**Conclusión:** TC001 confirma que la etiqueta "Vencida" aparece en la tarea vencida,
pero no prueba que *sólo* aparezca ahí. Para cubrir la consigna hace falta una aserción
negativa sobre las otras cuatro filas, con selectores por texto o por clase en vez de
XPath posicional. Los tests E2E propios del repo (`e2e/tests/vencidas.spec.ts`) son el
lugar natural para eso.

## Nota sobre el entorno durante la corrida

A las 12:25:36 se levantó un segundo cliente de TestSprite sobre la misma carpeta y
reconfiguró el proyecto a modo **backend** (`testsprite_tests/tmp/config.json` con
`type: backend` y un `projectKey` distinto), regenerando `code_summary.yaml` y
`standard_prd.json`. Por eso los archivos de `tmp/` ya no reflejan la configuración
frontend con la que se generaron estos dos casos. Los artefactos de esta carpeta son
copias tomadas antes de cada sobrescritura.
