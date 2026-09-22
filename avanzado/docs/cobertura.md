# Cobertura de la spec `prioridad-y-fecha-limite`

Esta tabla no pregunta *¿los tests pasan?* — pasan: **44 en verde**. Pregunta otra cosa:

> **¿Qué comprobaron esos 44 tests, y dónde miraron para comprobarlo?**

---

## Las tres cosas que puede mirar un test

| Dónde mira | Qué prueba de verdad |
|---|---|
| **La API** | Que el servidor calcule y devuelva bien los datos |
| **El HTML** | Que el servidor emita el markup esperado |
| **La base** | Que lo que se guardó sea lo que se pidió guardar |
| **El navegador** | Que una persona frente a la pantalla vea lo que el criterio pide |

Los 44 tests usan las tres primeras. **Ninguno usa la cuarta.**

---

## Página web — 15 tests

| Criterio de aceptación | Test que lo cubre | Dónde mira |
|---|---|---|
| Cada tarea muestra prioridad y fecha límite | `test_pagina_muestra_prioridad_y_fecha_limite` | El HTML |
| **Las vencidas se ven distintas de las no vencidas** | `test_pagina_marca_las_mismas_vencidas_que_la_api` | **El HTML: `class="overdue"`** |
| El alta preselecciona `media` y acepta prioridad y fecha | `test_formulario_de_alta_preselecciona_media`, `test_alta_desde_la_pagina_con_prioridad_y_fecha` | El HTML |
| Crear sin fecha la guarda con `due_date` null | `test_alta_desde_la_pagina_sin_fecha_la_guarda_nula` | El HTML y la API |
| Hay controles de filtro y de orden | `test_pagina_filtra_igual_que_la_api_y_refleja_los_controles` | El HTML |
| Aplicar los controles navega con los query params | `test_pagina_ordena_igual_que_la_api`, `test_pagina_con_opciones_todas_muestra_todas_las_tareas` | El HTML |
| Abrir la URL filtrada refleja los controles | `test_pagina_marca_el_checkbox_de_vencidas` | El HTML |
| Sin coincidencias, un mensaje propio | `test_pagina_sin_coincidencias_muestra_mensaje_propio`, `test_pagina_con_base_vacia_sin_filtros_muestra_mensaje_original` | El HTML |
| Completar y borrar siguen funcionando | `test_completar_y_borrar_desde_la_pagina_siguen_funcionando` | El HTML y la API |

**Quince tests de la página. Cero navegadores.** Todos parsean el HTML que devuelve el servidor.

---

## La fila que se rompe

El criterio dice:

> *"Las tareas vencidas se ven distintas de las no vencidas."*

El test verifica que el `<li>` salga con `class="overdue"`. Eso prueba que **el servidor decide bien quién está vencida** — que no es poco, y es correcto.

Pero *verse distinta* no lo produce la clase: lo producen dos reglas de CSS en `app/templates/index.html`.

```css
li.overdue { background: #fef3f2; border-left: 3px solid #d92d20; padding-left: .6rem; }
li.overdue .due, li .overdue-label { color: #b42318; font-weight: 600; }
```

Borrá esas dos líneas:

| | Resultado |
|---|---|
| `python -m pytest` | **44 passed** |
| La página en el navegador | La vencida se ve **idéntica** al resto |

El criterio queda incumplido, es visible a simple vista, y **no aparece en rojo en ningún reporte.**

El test no está mal escrito. Está mirando el lugar equivocado.

---

## API, orden, filtros y datos — 29 tests

Acá **no hay hueco**. Se revisó criterio por criterio, incluidos los bordes finos:

- `completed=false` y `completed=true` en el mismo test
- `overdue=true&completed=true` devolviendo vacío
- El desempate por `id` cuando dos tareas comparten fecha
- Un `422` por cada query param inválido
- La migración sobre una base con el esquema viejo, y arrancar dos veces sin duplicar

La API está bien cubierta. **Contra lo que alguien escribió en la spec.**

---

## Lo que no tiene ni un test, porque nadie lo pidió

La spec lo dice ella misma, en "Fuera de alcance":

1. Editar tareas existentes desde la página
2. Filtro por rango de fechas límite
3. Dirección de orden configurable
4. Hora en la fecha límite, zonas horarias por usuario, recordatorios
5. Paginación, filtrado con JavaScript
6. Cambios a `/ui/tasks/{id}/complete` y `/ui/tasks/{id}/delete`
7. Refactors no pedidos (`Depends()`, `APIRouter`, `/health`)
8. Tests para el código que ya existía

Y tres decisiones tomadas al cerrar la spec, ninguna con un test que las fije:

- `overdue=false` no filtra nada
- **"Hoy" es la fecha local del servidor**
- Los query params inválidos de `/` devuelven `422`

---

## Lo que propone una herramienta que lee el código

TestSprite generó el PRD leyendo `app/` (está en `testsprite_tests/standard_prd.json`) y levantó **nueve limitaciones** que nadie le pidió buscar:

| # | Lo que levanta | ¿Es cobertura? |
|---|---|---|
| 1 | Ningún endpoint tiene autenticación | Sí — fuera de alcance |
| 2 | `GET /tasks` no tiene paginación | Sí — fuera de alcance |
| 3 | No existe `/health` | Sí — fuera de alcance |
| 4 | **`/ui/.../complete` y `/delete` no validan existencia: un id inexistente responde `303` igual que una operación exitosa** | **Sí — bug real, sin test** |
| 5 | El repositorio es global de módulo en vez de `Depends()` | No — opinión de diseño |
| 6 | El `HTTPException` de 404 está repetido en cuatro handlers | No — opinión de diseño |
| 7 | Los handlers no usan `APIRouter` ni tienen docstrings | No — opinión de diseño |
| 8 | `PUT /tasks/{id}` se comporta como update parcial | Discutible — semántica |
| 9 | **El filtro `overdue` usa la fecha local del servidor** | Depende |

**Cinco de nueve son cobertura. Tres son opinión de refactor.** La herramienta propone; decidir cuáles importan sigue siendo trabajo de una persona.

### El número 9 merece un párrafo

TestSprite levanta como riesgo que las vencidas dependan de la zona horaria del servidor.

Y la spec, en sus decisiones de cierre, ya dice: *"Hoy es la fecha local del servidor"*.

**No es un hallazgo: es una decisión que alguien tomó a conciencia y escribió.** Eso es exactamente para lo que sirve tener la decisión anotada — permite descartar la alerta en cinco segundos, con fundamento, en vez de discutirla de nuevo.

Lo que la spec no anotó en ningún lado es que un criterio con efecto visible en la página necesita un test que abra el navegador.

---

## El resumen

| | |
|---|---|
| Tests que corren | 44 |
| Tests que pasan | 44 |
| Tests que abren un navegador | **0** |
| Criterios probados mirando el HTML en vez de lo que se ve | **1** (y es visible a simple vista) |
| Ítems fuera de alcance sin ningún test | 8 |
| Decisiones de la spec sin ningún test | 3 |

**Un test en verde prueba solamente lo que alguien eligió probar.**

Y lo que se eligió probar no lo decidió el agente: lo decidió `CLAUDE.md`, que sobre pruebas dice una sola cosa —*"tests con pytest en `tests/`"*— y nunca dice que algo tenga que abrir un navegador.
