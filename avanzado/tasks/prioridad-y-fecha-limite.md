# Tasks — Prioridad y fecha límite en las tareas

Derivadas de [`plans/prioridad-y-fecha-limite.md`](../plans/prioridad-y-fecha-limite.md), que
implementa [`specs/prioridad-y-fecha-limite.md`](../specs/prioridad-y-fecha-limite.md).

Cada task deja la app andando y suma sus propios tests en `tests/test_prioridad_fecha_limite.py`,
para que se pueda verificar sola con `python -m pytest` (parado en `avanzado/`). Los tests usan una
base en `tmp_path`: nunca tocan el `tasks.db` real.

## Tasks

1. [ ] **Infraestructura de tests.**
   - `requirements.txt`: sumar `pytest` y `httpx2`, con el mismo comentario que en `intermedio/`.
   - `tests/conftest.py`: fixture `db_path` (redirige `app.database.DB_PATH` a `tmp_path`) y fixture `client` (`TestClient` sobre esa base).
   - `tests/test_prioridad_fecha_limite.py`: un test de humo: `GET /tasks` responde `200` con las 5 tareas sembradas.
   - **Verificación:** `python -m pytest` pasa y `tasks.db` no cambia su fecha de modificación.

2. [ ] **Migración de la base.**
   - `app/database.py`: `_migrate(conn)` agrega `priority TEXT NOT NULL DEFAULT 'media'` y `due_date TEXT` solo si faltan (`PRAGMA table_info`), cada columna por separado. `init_db()` la llama entre el `CREATE TABLE` y `_seed_if_empty()`. El `CREATE TABLE` y `_SEED_TASKS` no cambian.
   - Todavía no se leen ni escriben las columnas desde la app.
   - **Tests** (leyendo la base con `sqlite3`, porque la API aún no expone los campos):
     - base nueva → las 5 tareas sembradas tienen `priority = 'media'` y `due_date IS NULL`;
     - base con el esquema viejo y tareas armada a mano → al arrancar, mismos `id`, `title`, `description`, `completed` y `created_at`, con `media` y `NULL`;
     - arrancar dos veces sobre la misma base → sin error y sin cambios en los datos.
   - **Verificación manual:** copiar `tasks.db`, arrancar `uvicorn app.main:app` sobre la base real y confirmar que la página y `GET /tasks` siguen iguales.

3. [ ] **Prioridad y fecha límite en el alta y la lectura de la API.**
   - `app/schemas.py`: `Priority(StrEnum)`, alias `DueDate` (`strict=True`), campos nuevos en `TaskCreate` y en `Task`.
   - `app/repository.py`: `_row_to_task` lee las columnas nuevas; `create` las escribe.
   - **Tests** (criterios de *Modelo y API — alta, lectura y edición*):
     - `POST` sin los campos → `media` / `null`;
     - `POST` con `alta` / `2026-10-01` → devuelve esos valores;
     - `priority` en `urgente` o `null` → `422` y la tarea no se crea;
     - `due_date` en `01/10/2026`, `2026-10-01T10:00:00`, `2026-10-01T00:00:00` o `0` → `422`;
     - `due_date` pasada → `201`;
     - `GET /tasks` y `GET /tasks/{id}` incluyen los dos campos;
     - el seed sale con `media` / `null` por la API.

4. [ ] **Edición de prioridad y fecha límite por la API.**
   - `app/schemas.py`: campos nuevos en `TaskUpdate`, con el validador que rechaza `priority: null`.
   - `app/repository.py`: `update` escribe `priority` y `due_date`.
   - **Tests:**
     - `PUT` con solo `priority: baja` → cambia eso y nada más;
     - `PUT` con `due_date: null` → saca la fecha;
     - `PUT` con `priority: null` o `urgente` → `422` y la tarea no cambia (se verifica con `GET`);
     - `PATCH /tasks/{id}/complete` no cambia `priority` ni `due_date`.

5. [ ] **Filtros en `GET /tasks`.**
   - `app/schemas.py`: `TaskFilters` con `priority` y `completed`, más el validador que convierte `""` en `None`.
   - `app/repository.py`: `list_all(filters)` arma el `WHERE` con parámetros `?`.
   - `app/main.py`: `GET /tasks` recibe `Annotated[TaskFilters, Query()]`.
   - **Tests:**
     - `?priority=alta` incluye las completadas;
     - `?completed=false` y `?completed=true`;
     - combinación de los dos filtros;
     - `?priority=urgente` → `422`;
     - filtro sin coincidencias → `200` con `[]`;
     - `?priority=` → sin filtro.

6. [ ] **Orden por prioridad en `GET /tasks`.**
   - `app/schemas.py`: `sort: Literal["priority"] | None` en `TaskFilters`.
   - `app/repository.py`: `ORDER BY` desde un diccionario cerrado (`id` o el `CASE` de prioridad + `id`).
   - **Tests:**
     - sin `sort` → por `id`;
     - `?sort=priority` con tareas creadas en orden `baja`, `alta`, `media`, `alta` → `alta`, `alta`, `media`, `baja`, y las dos `alta` por `id`;
     - `sort` combinado con los dos filtros;
     - `?sort=due_date` → `422`.

7. [ ] **La página muestra la prioridad, la fecha límite y las vencidas.**
   - `app/main.py`: `GET /` pasa `today` a la plantilla.
   - `app/templates/index.html`: prioridad y fecha en cada tarea, etiqueta "Vencida" con la clase `.overdue`, y el CSS.
   - **Tests** sobre el HTML de `GET /`, con fechas lejanas (`2000-01-01`, `2999-12-31`) para no depender del día:
     - se muestran la prioridad y la fecha;
     - la tarea pendiente con fecha pasada tiene "Vencida";
     - no la tienen la completada con fecha pasada, la que vence hoy, la de fecha futura ni la que no tiene fecha.
   - **Verificación manual:** mirar la página en el navegador.

8. [ ] **Prioridad y fecha límite en el form de alta de la página.**
   - `app/templates/index.html`: `<select name="priority">` con `media` preseleccionada, e `<input type="date" name="due_date">`.
   - `app/main.py`: `POST /ui/tasks` recibe `priority` y `due_date`; helper `_parse_due_date` (vacía → `None`; inválida → `HTTPException` `422` con el mensaje en español).
   - **Tests:**
     - alta con `alta` / `2026-10-01` → verificada con `GET /tasks/{id}`;
     - alta con fecha vacía → `due_date: null`;
     - alta sin `priority` → `media`;
     - fecha `01/10/2026` → `422`.

9. [ ] **Controles de filtro y orden en la página.**
   - `app/main.py`: `GET /` recibe `Annotated[TaskFilters, Query()]` y pasa `filters` y `priorities`.
   - `app/templates/index.html`: form GET con los tres `<select>` y "Aplicar", los valores actuales seleccionados, y los dos mensajes de lista vacía.
   - **Tests:**
     - `/?priority=alta&completed=false&sort=priority` muestra las mismas tareas, en el mismo orden, que `GET /tasks` con esos parámetros;
     - los `<select>` salen con esos valores seleccionados;
     - `/?priority=&completed=&sort=` muestra todo;
     - con tareas y sin coincidencias → "Ninguna tarea coincide con el filtro.";
     - sin tareas y sin filtros → "No hay tareas todavía.".

10. [ ] **Mantener los filtros después de crear, completar o borrar desde la página.**
    - `app/main.py`: helper `_index_url(filters)` (orden fijo `priority`, `completed`, `sort`; booleanos como `true`/`false`); `GET /` pasa `query_string`; los tres `POST /ui/...` reciben `TaskFilters` desde la query y redirigen a `_index_url`.
    - `app/templates/index.html`: `?{{ query_string }}` en el `action` de los tres forms POST.
    - **Tests:**
      - estando en `?priority=alta&completed=false&sort=priority`, cada una de las tres acciones responde `303` con `Location` igual a `/?priority=alta&completed=false&sort=priority`;
      - las tres, sin filtros → `Location: /`;
      - el HTML de `GET /` con filtros tiene la query en los `action` de los forms.

11. [ ] **Verificación final contra el spec.**
    - `python -m pytest` completo en verde.
    - Recorrer los criterios de aceptación del spec uno por uno y marcar cuál test (o qué verificación manual) cubre cada uno.
    - A mano en el navegador, sobre una **copia** del `tasks.db` real con el esquema viejo:
      - la migración conserva las tareas;
      - alta con prioridad y fecha;
      - filtros y orden desde los controles;
      - completar y borrar con filtros puestos;
      - marca de vencida.
    - Confirmar que no se tocó nada fuera de los archivos del plan (`git status`), en particular ningún `CLAUDE.md`.
    - Sin commit propio salvo que aparezca algo para corregir.

> Regla: si una tarea no se puede verificar por separado, es demasiado grande — partila en dos.
