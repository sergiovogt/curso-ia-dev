# Spec — Prioridad y fecha límite en las tareas

## Contexto

Hoy todas las tareas pesan lo mismo y no tienen vencimiento, así que en una lista larga no hay
forma de ver qué es urgente. Esta feature agrega prioridad y fecha límite a cada tarea, y permite
filtrar y ordenar por ellas tanto desde la API como desde la página web.

## Alcance

- Dos campos nuevos en la tarea: `priority` (`baja` | `media` | `alta`, obligatoria, default
  `media`) y `due_date` (solo fecha `YYYY-MM-DD`, opcional, se aceptan fechas pasadas).
- Los campos se leen en todas las respuestas de la API y se cargan al crear (`POST /tasks`) y al
  editar (`PUT /tasks/{id}`).
- `GET /tasks` acepta filtros por prioridad y por estado de completada, que se pueden combinar, y
  un orden por prioridad.
- La página muestra la prioridad y la fecha límite de cada tarea, marca las vencidas, permite
  cargar ambos campos al crear una tarea y permite filtrar y ordenar la lista con los mismos
  criterios que la API. Crear, completar o borrar una tarea desde la página vuelve a la misma vista
  filtrada y ordenada.
- Una `tasks.db` existente se actualiza al arrancar la app, sin perder tareas: las que ya estaban
  quedan con prioridad `media` y sin fecha límite.

## Criterios de aceptación

### Modelo y API — alta, lectura y edición

- [ ] `POST /tasks` sin `priority` ni `due_date` crea la tarea con `"priority": "media"` y `"due_date": null`, y responde `201`.
- [ ] `POST /tasks` con `"priority": "alta"` y `"due_date": "2026-10-01"` crea la tarea con esos valores, y la respuesta los incluye tal cual.
- [ ] `POST /tasks` con `"priority": "urgente"` (u otro valor fuera de `baja`/`media`/`alta`) responde `422` y no crea la tarea.
- [ ] `POST /tasks` con `"priority": null` responde `422`.
- [ ] `POST /tasks` con `"due_date": "01/10/2026"` o `"due_date": "2026-10-01T10:00:00"` responde `422`.
- [ ] `POST /tasks` con una `due_date` anterior a hoy crea la tarea normalmente (`201`).
- [ ] `GET /tasks` y `GET /tasks/{id}` incluyen `priority` y `due_date` en cada tarea, con `due_date` en formato `YYYY-MM-DD` o `null`.
- [ ] `PUT /tasks/{id}` con solo `{"priority": "baja"}` cambia la prioridad y deja `due_date`, `title`, `description` y `completed` sin cambios.
- [ ] `PUT /tasks/{id}` con `{"due_date": null}` le saca la fecha límite a la tarea.
- [ ] `PUT /tasks/{id}` con `{"priority": null}` o una prioridad inválida responde `422` y no modifica la tarea.
- [ ] `PATCH /tasks/{id}/complete` no cambia `priority` ni `due_date`.

### API — filtros y orden en `GET /tasks`

- [ ] `GET /tasks?priority=alta` devuelve solo las tareas de prioridad `alta`, incluidas las completadas.
- [ ] `GET /tasks?completed=false` devuelve solo las tareas no completadas; `?completed=true`, solo las completadas.
- [ ] `GET /tasks?priority=alta&completed=false` devuelve solo las tareas que cumplen ambas condiciones.
- [ ] `GET /tasks?priority=urgente` responde `422`.
- [ ] Un filtro que no coincide con ninguna tarea devuelve `200` con `[]`.
- [ ] `GET /tasks` sin `sort` devuelve las tareas ordenadas por `id` ascendente (igual que hoy).
- [ ] `GET /tasks?sort=priority` devuelve primero las `alta`, luego las `media` y luego las `baja`; dentro de cada prioridad, por `id` ascendente.
- [ ] `GET /tasks?sort=priority&priority=media&completed=false` aplica los filtros y el orden a la vez.
- [ ] `GET /tasks?sort=due_date` (o cualquier valor de `sort` distinto de `priority`) responde `422`.

### Página web (`/`)

- [ ] Cada tarea de la lista muestra su prioridad y, si tiene, su fecha límite en formato `YYYY-MM-DD`. Si no tiene fecha límite, no se muestra nada sobre la fecha.
- [ ] Una tarea **no completada** con fecha límite anterior a la fecha actual se ve marcada como vencida, y es distinguible de una que no lo está sin tener que leer la fecha.
- [ ] No se marcan como vencidas las tareas completadas, las que vencen hoy ni las que no tienen fecha límite.
- [ ] El formulario de alta tiene un selector de prioridad con `baja`, `media` y `alta`, con `media` preseleccionada, y un campo de fecha límite opcional.
- [ ] Crear una tarea desde la página con prioridad `alta` y fecha `2026-10-01` la deja con esos valores (verificable con `GET /tasks/{id}`).
- [ ] Crear una tarea desde la página dejando la fecha vacía la deja con `due_date: null`.
- [ ] La página tiene controles para filtrar por prioridad (todas / `baja` / `media` / `alta`), por estado (todas / pendientes / completadas) y para ordenar (por creación / por prioridad).
- [ ] Aplicar los controles da el mismo conjunto y el mismo orden de tareas que `GET /tasks` con los parámetros equivalentes.
- [ ] Los criterios aplicados se reflejan en la URL (`/?priority=alta&completed=false&sort=priority`): abrir esa URL directamente muestra la lista ya filtrada y ordenada, con los controles mostrando esos valores.
- [ ] Estando en `/?priority=alta&completed=false&sort=priority`, crear, completar o borrar una tarea desde la página vuelve a `/?priority=alta&completed=false&sort=priority`, con la lista filtrada y ordenada con esos criterios y los controles mostrando esos valores. Lo mismo vale para cualquier otra combinación de filtros y orden.
- [ ] Estando en `/` sin filtros, crear, completar o borrar una tarea vuelve a `/` sin filtros, como hoy.
- [ ] Si hay tareas pero ninguna coincide con el filtro, la página muestra un mensaje que dice que ninguna tarea coincide con el filtro, distinto de «No hay tareas todavía.».

### Datos

- [ ] Con `tasks.db` borrado, al arrancar la app las 5 tareas sembradas aparecen con `"priority": "media"` y `"due_date": null`, sin otros cambios.
- [ ] Con una `tasks.db` creada por la versión anterior de la app (sin las columnas nuevas), al arrancar la app no hay error, todas las tareas que ya existían siguen estando con el mismo `id`, `title`, `description`, `completed` y `created_at`, y aparecen con `"priority": "media"` y `"due_date": null`.
- [ ] Después de esa actualización, esas tareas se pueden filtrar, ordenar y editar (`PUT /tasks/{id}`) igual que una tarea nueva.
- [ ] Reiniciar la app sobre una `tasks.db` que ya fue actualizada no da error ni cambia ningún dato.

## Fuera de alcance

- Editar la prioridad o la fecha límite de una tarea existente desde la página (se hace con `PUT /tasks/{id}`).
- Ordenar por fecha límite o elegir la dirección del orden (asc/desc).
- Filtrar por vencidas o por rango de fechas límite, y filtrar por varias prioridades a la vez (`?priority=alta&priority=media`).
- Fecha límite con hora o zona horaria.
- Cambiar las tareas sembradas para que tengan prioridades o fechas límite variadas.
- Paginación, `APIRouter`, `Depends()` u otros puntos de `docs/CODING_STANDARDS.md` que el código no cumple hoy.

## Preguntas abiertas

_Ninguna. Todas las ambigüedades se cerraron antes de redactar la spec._
