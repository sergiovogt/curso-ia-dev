# Spec — Prioridad y fecha límite en tareas

## Contexto

Hoy todas las tareas pesan lo mismo y no tienen vencimiento: no hay forma de saber qué atender primero
ni qué está atrasado. Esta feature agrega prioridad y fecha límite a cada tarea, y permite filtrar y
ordenar por esos datos tanto desde la API JSON como desde la página web.

## Alcance

- Dos campos nuevos en la tarea:
  - `priority`: `alta`, `media` o `baja`. Opcional al crear; si no se manda, vale `media`. Nunca es null.
  - `due_date`: fecha sin hora (`YYYY-MM-DD`), opcional (puede ser null). Se aceptan fechas pasadas.
- Los campos se pueden enviar al crear (`POST /tasks`) y modificar al actualizar (`PUT /tasks/{id}`),
  y aparecen en todas las respuestas que devuelven tareas.
- `GET /tasks` acepta filtros y orden por query params:
  - `priority=alta|media|baja`
  - `completed=true|false`
  - `overdue=true`
  - `sort_by=priority|due_date`
  - Los filtros se combinan entre sí (se aplican todos a la vez).
- Definición de **vencida**: tarea no completada cuya `due_date` es anterior a la fecha de hoy
  (fecha local del servidor). Una tarea que vence hoy no está vencida.
- Página web (`/`):
  - Cada tarea muestra su prioridad y su fecha límite (si tiene).
  - Las tareas vencidas se distinguen visualmente del resto.
  - El formulario de alta permite elegir prioridad y fecha límite.
  - Controles de filtro (prioridad, estado, solo vencidas) y orden, que se aplican con un form `GET`
    usando los mismos query params que la API.
- Bases existentes y seed:
  - Una `tasks.db` creada antes de esta feature se actualiza sola al arrancar la app, sin perder tareas.
  - Las tareas de ejemplo del seed traen prioridades y fechas límite variadas.

## Criterios de aceptación

### Modelo y API — creación y actualización

- [ ] `POST /tasks` con `{"title": "x"}` devuelve `201` con `"priority": "media"` y `"due_date": null`.
- [ ] `POST /tasks` con `{"title": "x", "priority": "alta", "due_date": "2026-12-31"}` devuelve `201`
      con esos mismos valores, y `GET /tasks/{id}` los devuelve igual.
- [ ] `POST /tasks` con `"due_date"` anterior a hoy devuelve `201` (no se rechazan fechas pasadas).
- [ ] `POST /tasks` con `"priority": "urgente"` devuelve `422`.
- [ ] `POST /tasks` con `"priority": null` devuelve `422`.
- [ ] `POST /tasks` con `"due_date": "31/12/2026"` o `"due_date": "2026-12-31T10:00:00"` devuelve `422`.
- [ ] `PUT /tasks/{id}` con `{"priority": "baja"}` cambia solo la prioridad; `title`, `description`,
      `completed` y `due_date` quedan como estaban.
- [ ] `PUT /tasks/{id}` con `{"due_date": null}` sobre una tarea con fecha límite la deja sin fecha.
- [ ] `PUT /tasks/{id}` con `{"priority": null}` devuelve `422`.
- [ ] `PATCH /tasks/{id}/complete` y `GET /tasks/{id}` incluyen `priority` y `due_date` en la respuesta.

### API — filtros

- [ ] `GET /tasks?priority=alta` devuelve solo las tareas con prioridad `alta`, completadas incluidas.
- [ ] `GET /tasks?priority=urgente` devuelve `422`.
- [ ] `GET /tasks?completed=false` devuelve solo las tareas pendientes; `completed=true`, solo las completadas.
- [ ] `GET /tasks?overdue=true` devuelve solo tareas no completadas con `due_date` anterior a hoy:
      no incluye tareas sin fecha, ni con fecha de hoy o futura, ni completadas con fecha pasada.
- [ ] `GET /tasks?priority=alta&overdue=true` devuelve solo las tareas que cumplen ambas condiciones.
- [ ] `GET /tasks?overdue=true&completed=true` devuelve una lista vacía con `200`.
- [ ] `GET /tasks` sin parámetros devuelve todas las tareas ordenadas por `id`, igual que hoy.

### API — orden

- [ ] `GET /tasks?sort_by=priority` devuelve primero las `alta`, luego las `media`, luego las `baja`;
      dentro de la misma prioridad, por `id` ascendente.
- [ ] `GET /tasks?sort_by=due_date` devuelve las tareas con fecha de la más próxima (más antigua) a la
      más lejana; las tareas sin fecha van al final; empates (misma fecha o ambas sin fecha) por `id` ascendente.
- [ ] `GET /tasks?sort_by=titulo` devuelve `422`.
- [ ] Filtro y orden se combinan: `GET /tasks?completed=false&sort_by=due_date` devuelve solo pendientes,
      en el orden de fecha descripto arriba.

### Página web

- [ ] Cada tarea del listado muestra su prioridad y, si tiene, su fecha límite en formato `YYYY-MM-DD`.
      Las tareas sin fecha límite no muestran fecha.
- [ ] Las tareas vencidas (según la definición de Alcance) se ven distintas de las no vencidas; una tarea
      completada con fecha pasada no se marca como vencida.
- [ ] El formulario de alta tiene un selector de prioridad con `media` preseleccionada y un campo de fecha
      opcional. Crear una tarea con prioridad `alta` y fecha `2026-12-31` la muestra en el listado con esos datos.
- [ ] Crear una tarea desde la página sin completar la fecha la guarda con `due_date` null.
- [ ] La página tiene controles para filtrar por prioridad (todas / alta / media / baja), por estado
      (todas / pendientes / completadas), solo vencidas, y para ordenar (creación / prioridad / fecha límite).
- [ ] Aplicar los controles navega a `/` con los query params `priority`, `completed`, `overdue` y `sort_by`
      (ej. `/?priority=alta&sort_by=due_date`), y el listado muestra el mismo resultado que `GET /tasks`
      con esos parámetros.
- [ ] Abrir directamente `/?priority=alta&completed=false` muestra el listado filtrado y los controles
      reflejan los filtros aplicados.
- [ ] Si hay tareas pero ninguna coincide con los filtros, la página muestra un mensaje que lo indica,
      distinto de "No hay tareas todavía.".
- [ ] Completar o borrar una tarea desde la página sigue funcionando como hoy.

### Datos existentes y seed

- [ ] Arrancar la app sobre una `tasks.db` creada con el esquema anterior no da error, conserva todas las
      tareas y les asigna `priority = media` y `due_date = null`.
- [ ] Arrancar la app dos veces seguidas sobre la misma base no da error ni duplica tareas.
- [ ] Con una base nueva, el seed crea las mismas 5 tareas de hoy con, entre todas: las tres prioridades
      representadas, al menos una tarea pendiente vencida, al menos una pendiente con fecha límite futura
      y al menos una sin fecha límite. Las fechas son fijas (no calculadas a partir de hoy).

### Tests automatizados

- [ ] `python -m pytest`, corrido desde `avanzado/`, pasa sin fallos.
- [ ] Hay al menos un test por cada criterio de las secciones "Modelo y API", "API — filtros",
      "API — orden" y "Datos existentes y seed".
- [ ] En "Página web" hay tests para: prioridad y fecha visibles, marca de vencida (incluida la completada
      con fecha pasada que no se marca), alta con y sin fecha, filtros aplicados por query string con los
      controles reflejándolos, y mensaje de sin coincidencias.
- [ ] Los tests de vencidas pasan en cualquier fecha en que se corran (no dependen de que hoy sea un día
      en particular).
- [ ] Correr los tests no crea, modifica ni borra el `tasks.db` del nivel.

## Fuera de alcance

- Editar tareas existentes desde la página (cambiar prioridad, fecha u otros campos). Solo por API.
- Filtro por rango de fechas límite (`desde` / `hasta`).
- Dirección de orden configurable (asc/desc) y orden por otros campos.
- Hora en la fecha límite, zonas horarias por usuario, recordatorios o notificaciones.
- Paginación, filtrado del lado del navegador con JavaScript.
- Cambios a las rutas `/ui/tasks/{id}/complete` y `/ui/tasks/{id}/delete`.
- Refactors no pedidos (`Depends()`, `APIRouter`, `/health`, etc.) aunque figuren en `docs/CODING_STANDARDS.md`.
- Tests para el código que ya existía y que esta feature no toca (por ejemplo, `DELETE /tasks/{id}`).

## Preguntas abiertas

Ninguna. Decisiones tomadas al cerrar el spec, por si alguna hay que revisar:

- `overdue=false` no filtra nada (equivale a no mandar el parámetro).
- "Hoy" es la fecha local del servidor.
- Los valores inválidos en los query params de `/` se tratan igual que en la API (`422`).
