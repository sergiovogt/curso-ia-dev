# Spec — Prioridad y fecha límite en tareas

## Contexto

El gestor de tareas actual solo permite título, descripción y estado completado. Para priorizar el trabajo y ver qué vence pronto, las tareas necesitan prioridad y fecha límite, con la posibilidad de filtrar y ordenar tanto desde la página como desde la API JSON.

## Alcance

- Agregar los campos **prioridad** (`alta` | `media` | `baja`) y **fecha límite** (fecha opcional, sin hora) al modelo de tarea, persistencia SQLite y schemas Pydantic.
- Migrar tareas existentes (incluidas las 5 del seed) asignándoles prioridad `media` y fecha límite `null`.
- Formulario de alta en la página: el usuario puede elegir prioridad (default `media`) y fecha límite (opcional).
- API `POST /tasks` y `POST /ui/tasks`: aceptan prioridad y fecha límite con los mismos defaults y validaciones.
- Listado en página (`GET /`) y API (`GET /tasks`): soportan filtro por prioridad (una o varias), filtro por fecha límite (rango, vencidas, sin fecha) y orden por prioridad o por fecha límite.
- Orden por defecto sin parámetros: prioridad descendente (alta → media → baja), desempate por fecha límite ascendente (más próxima primero; sin fecha al final).
- Visualización en la página: cada tarea muestra prioridad y fecha límite; las vencidas (fecha límite anterior a **hoy en UTC-3** y no completadas) se destacan visualmente.
- Definición de **hoy**: fecha calendario en UTC-3 (`datetime.now(timezone(timedelta(hours=-3))).date()`), usada en filtro `vencidas`, badge de UI y tests.
- Controles de filtro y orden en la página que reflejan los query params soportados por el backend.
- Validaciones que impiden modificar `prioridad` y `fecha_limite` después de crear la tarea (API y UI).

## Criterios de aceptación

### Modelo y migración

- [ ] Toda tarea expuesta por la API incluye `prioridad` (`alta`, `media` o `baja`) y `fecha_limite` (`YYYY-MM-DD` o `null`).
- [ ] Tras migrar una base con las 5 tareas del seed (sin columnas nuevas), cada una queda con `prioridad=media` y `fecha_limite=null`.
- [ ] `POST /tasks` con body `{"title": "X"}` crea la tarea con `prioridad=media` y `fecha_limite=null`.
- [ ] `POST /tasks` con `prioridad=alta` y `fecha_limite=2026-07-15` persiste y devuelve esos valores.
- [ ] `POST /tasks` con `prioridad=invalida` responde 422; con `fecha_limite` en formato distinto de `YYYY-MM-DD` responde 422.

### Alta desde la UI

- [ ] El formulario de nueva tarea incluye selector de prioridad (default `media`) e input de fecha límite (opcional, vacío = sin fecha).
- [ ] Enviar el formulario sin tocar prioridad ni fecha crea una tarea con `prioridad=media` y `fecha_limite=null`.

### Inmutabilidad post-creación (API y UI)

- [ ] `PUT /tasks/{id}` con body que incluye `prioridad` responde **422** con mensaje que indica que el campo no es editable; `prioridad` y `fecha_limite` de la tarea en base no cambian.
- [ ] `PUT /tasks/{id}` con body que incluye `fecha_limite` responde **422** con mensaje que indica que el campo no es editable; los valores persistidos no cambian.
- [ ] `PUT /tasks/{id}` con body que incluye ambos campos responde **422**; ninguno de los dos se modifica aunque el resto del payload (p. ej. `title`) sea válido.
- [ ] `PUT /tasks/{id}` sin `prioridad` ni `fecha_limite` en el body sigue permitiendo actualizar `title`, `description` y `completed` con normalidad.
- [ ] `PATCH /tasks/{task_id}/complete` y `POST /ui/tasks/{id}/complete` no alteran `prioridad` ni `fecha_limite` de la tarea.
- [ ] La página no expone controles para editar prioridad ni fecha límite en tareas ya creadas (solo lectura en el listado).

### Filtro por prioridad (UI y `GET /tasks`)

- [ ] Sin parámetro de prioridad, el listado incluye tareas de todas las prioridades, completadas incluidas.
- [ ] `?prioridad=alta` devuelve solo tareas con prioridad alta, completadas incluidas.
- [ ] `?prioridad=alta,media` devuelve tareas con prioridad alta o media, completadas incluidas.
- [ ] `?prioridad=alta,baja` no devuelve tareas de prioridad media.

### Filtro por fecha límite (UI y `GET /tasks`)

- [ ] `?fecha_desde=2026-07-01&fecha_hasta=2026-07-31` devuelve solo tareas cuya `fecha_limite` cae en ese rango inclusive; tareas con `fecha_limite=null` quedan fuera.
- [ ] `?vencidas=1` devuelve solo tareas no completadas cuya `fecha_limite` es anterior a **hoy en UTC-3**; tareas con `fecha_limite` igual a hoy UTC-3 no se consideran vencidas; tareas completadas con fecha pasada no aparecen.
- [ ] `?sin_fecha=1` devuelve solo tareas con `fecha_limite=null`.
- [ ] Los filtros de prioridad y de fecha límite son combinables (intersección): `?prioridad=alta&vencidas=1` devuelve tareas que cumplen ambas condiciones.

### Orden (UI y `GET /tasks`)

- [ ] Sin parámetros de orden, la lista queda ordenada por prioridad descendente (alta, media, baja) y, a igual prioridad, por `fecha_limite` ascendente; tareas sin fecha límite van después de las que sí tienen, a igual prioridad.
- [ ] `?orden=prioridad&dir=asc` ordena prioridad baja → media → alta; `dir=desc` invierte.
- [ ] `?orden=fecha_limite&dir=asc` ordena por fecha más próxima primero; tareas con `fecha_limite=null` al final del listado.
- [ ] `?orden=fecha_limite&dir=desc` ordena por fecha más lejana primero; tareas con `fecha_limite=null` al final del listado.

### Visualización en la página

- [ ] Cada ítem de la lista muestra la prioridad y la fecha límite (o un texto equivalente cuando no hay fecha, p. ej. «Sin fecha límite»).
- [ ] Una tarea no completada con `fecha_limite` anterior a hoy UTC-3 muestra un indicador visual de vencida (badge, color u otro estilo distinguible) además de la fecha.
- [ ] Una tarea completada con fecha pasada no se marca como vencida visualmente.
- [ ] La página incluye controles para elegir filtro de prioridad (multi-selección), filtro de fecha (rango, vencidas, sin fecha) y criterio de orden; al aplicarlos, la URL refleja los query params y la lista coincide con `GET /tasks` usando los mismos params.

## Fuera de alcance

- Endpoints o formularios de edición de prioridad o fecha límite post-creación (la inmutabilidad se valida con 422 en API y ausencia de controles en UI; ver criterios de «Inmutabilidad post-creación»).
- Filtro u orden por estado completado, título u otros campos.
- Notificaciones, recordatorios o jobs por vencimiento.
- Soporte de hora en la fecha límite (solo fecha calendario).
- Paginación del listado.
- Cambios de estilo global de la app más allá de lo necesario para mostrar los nuevos campos, controles y el estado vencida.

## Preguntas abiertas

_(Ninguna — decisiones cerradas en la entrevista previa.)_
