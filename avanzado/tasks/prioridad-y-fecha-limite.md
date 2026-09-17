# Tasks — Prioridad y fecha límite en tareas

Derivadas de [`plans/prioridad-y-fecha-limite.md`](../plans/prioridad-y-fecha-limite.md), que implementa
[`specs/prioridad-y-fecha-limite.md`](../specs/prioridad-y-fecha-limite.md).

Cómo se verifica cada task, salvo que diga otra cosa: desde `avanzado/`, con las dependencias de
`requirements.txt` instaladas, `python -m pytest` pasa completo (los tests de la task y los de las
anteriores). Cada task deja la app arrancable y la página funcionando.

Diferencia con el template: no hay una task de tests separada al final. Según el plan, cada task trae
sus tests en el mismo commit, así ese commit se verifica solo.

## Tasks

1. [ ] **Infraestructura de tests**
   - `requirements.txt`: sumar `pytest>=8.3.0` y `httpx2>=2.12.0`, con el mismo comentario que en `intermedio/`.
   - `tests/conftest.py`: fixture `client` (`DB_PATH` apuntando a `tmp_path`, `with TestClient(app)`,
     `DELETE FROM tasks`) y fixture `seeded_client` (igual pero sin el `DELETE`).
   - `tests/test_api_tasks.py`: un primer test del comportamiento que no tiene que cambiar.
     `GET /tasks` sin parámetros devuelve todas las tareas ordenadas por `id`.
   - No toca código de `app/`.
   - Verificación: `pip install -r requirements.txt` y `python -m pytest` → 1 test pasa. El `mtime` de
     `tasks.db` no cambia.
   - Commit: `test(avanzado): agregar infraestructura de tests con base temporal`

2. [ ] **Columnas nuevas, migración y seed**
   - `app/database.py`:
     - Sumar `priority TEXT NOT NULL DEFAULT 'media'` y `due_date TEXT` al `CREATE TABLE`.
     - Agregar `_migrate(conn)` (`PRAGMA table_info` + `ALTER TABLE ADD COLUMN` para lo que falte),
       llamada antes de `_seed_if_empty`.
     - Pasar `_SEED_TASKS` a 6 campos con los valores de la tabla del plan.
   - No toca `schemas.py` ni `repository.py`: la API todavía no expone los campos, y el `INSERT` de
     `create` cae en los defaults de la columna.
   - `tests/test_database.py`, que lee las filas directo con `sqlite3`:
     - Una base con el esquema viejo y dos filas: después de `init_db()` conserva las dos filas, con
       `priority = 'media'` y `due_date` null.
     - `init_db()` dos veces seguidas sobre la misma base no falla ni duplica filas.
     - Base nueva (`seeded_client`): las 5 tareas del seed tienen exactamente la prioridad, el estado
       completada y la fecha de la tabla del plan.
   - Verificación: tests pasan. Además, arrancar `uvicorn app.main:app` sobre una copia de la `tasks.db`
     real y confirmar en `/` que siguen las 5 tareas.
   - Commit: `feat(avanzado): agregar columnas de prioridad y fecha limite con migracion`

3. [ ] **Prioridad en el modelo y la API**
   - `app/schemas.py`:
     - Agregar `Priority(StrEnum)`.
     - Agregar `priority: Priority = Priority.MEDIA` en `TaskCreate`.
     - Agregar `priority: Priority | None = None` en `TaskUpdate`, con un `field_validator` que rechaza
       `None` explícito con mensaje en español.
     - Agregar `priority: Priority` en `Task`.
   - `app/repository.py`: `_row_to_task`, `create` y `update` leen y escriben `priority`.
   - Tests en `tests/test_api_tasks.py`:
     - `POST` sin prioridad → `media`.
     - `POST` con `alta` → `alta`, y `GET /tasks/{id}` devuelve lo mismo.
     - `POST` con `"urgente"` → `422`.
     - `POST` con `null` → `422`.
     - `PUT` con `{"priority": "baja"}` cambia solo la prioridad.
     - `PUT` con `{"priority": null}` → `422`.
     - `PATCH /tasks/{id}/complete` incluye `priority`.
   - Commit: `feat(avanzado): agregar prioridad a las tareas en la API`

4. [ ] **Fecha límite en el modelo y la API**
   - `app/schemas.py`: `due_date: date | None = None` en `TaskCreate` y `TaskUpdate`, y `due_date: date | None` en `Task`.
   - `app/repository.py`: `_row_to_task` (con `date.fromisoformat` si no es null), `create` y `update`
     leen y escriben `due_date`.
   - Tests:
     - `POST` sin fecha → `null`.
     - `POST` con `2026-12-31` → mismo valor en la respuesta y en `GET /tasks/{id}`.
     - `POST` con fecha pasada (hoy - 1) → `201`.
     - `POST` con `"31/12/2026"` → `422`.
     - `POST` con `"2026-12-31T10:00:00"` → `422`.
     - `PUT` con `{"due_date": null}` borra la fecha.
     - `PUT` que solo manda `due_date` no cambia los demás campos.
     - `PATCH /tasks/{id}/complete` incluye `due_date`.
   - Commit: `feat(avanzado): agregar fecha limite a las tareas en la API`

5. [ ] **Filtros en `GET /tasks`**
   - `app/schemas.py`: modelo `TaskFilters` con `priority: Priority | None`, `completed: bool | None` y `overdue: bool = False`.
     Sin `sort_by` y sin el validador de strings vacíos todavía.
   - `app/repository.py`: `list_all(filters: TaskFilters | None = None)` arma el `WHERE` con parámetros `?`.
     Para vencidas: `completed = 0 AND due_date IS NOT NULL AND due_date < ?` con `date.today().isoformat()`.
   - `app/main.py`: `list_tasks` recibe `Annotated[TaskFilters, Query()]`. `index` sigue llamando `list_all()` sin filtros.
   - Tests. Juego de datos: pendiente vencida, pendiente que vence hoy, pendiente futura, pendiente sin fecha,
     completada con fecha pasada, en varias prioridades.
     - `?priority=alta` incluye las completadas.
     - `?priority=urgente` → `422`.
     - `?completed=false` y `?completed=true`.
     - `?overdue=true` devuelve solo la pendiente vencida.
     - `?priority=alta&overdue=true`.
     - `?overdue=true&completed=true` → lista vacía con `200`.
   - Commit: `feat(avanzado): filtrar tareas por prioridad, estado y vencidas`

6. [ ] **Orden en `GET /tasks`**
   - `app/schemas.py`: `SortBy(StrEnum)` y `sort_by: SortBy | None = None` en `TaskFilters`.
   - `app/repository.py`: dict `SortBy → ORDER BY` fijo (`CASE` de prioridad + `id`; `due_date IS NULL, due_date, id`).
     Sin `sort_by`, `ORDER BY id`.
   - Tests:
     - `?sort_by=priority`: orden `alta`, `media`, `baja`, con desempate por `id`.
     - `?sort_by=due_date`: de la más próxima a la más lejana, sin fecha al final, empates por `id`.
     - `?sort_by=titulo` → `422`.
     - `?completed=false&sort_by=due_date`.
   - Commit: `feat(avanzado): ordenar tareas por prioridad o fecha limite`

7. [ ] **Página: mostrar prioridad, fecha y vencidas**
   - `app/schemas.py`: `@property is_overdue` en `Task`.
   - `app/templates/index.html`:
     - `.meta` muestra la prioridad y "Vence: YYYY-MM-DD" solo si hay fecha.
     - Clase `overdue` en el `<li>` si `t.is_overdue`.
     - Estilos para `.overdue` y la etiqueta de prioridad.
   - Tests en `tests/test_web.py`:
     - La página muestra la prioridad de cada tarea y la fecha cuando existe.
     - Una tarea sin fecha no muestra "Vence".
     - Con el mismo juego de datos de la task 5, las tareas con clase `overdue` son exactamente las que
       devuelve `GET /tasks?overdue=true`, y la completada con fecha pasada no la tiene.
     - `GET /tasks` sigue sin exponer un campo `is_overdue`.
     - Completar y borrar desde `/ui/tasks/{id}/...` siguen redirigiendo con `303` y surten efecto.
   - Commit: `feat(avanzado): mostrar prioridad, fecha limite y vencidas en la pagina`

8. [ ] **Página: prioridad y fecha en el alta**
   - `app/templates/index.html`: `<select name="priority">` con `media` preseleccionada y `<input type="date" name="due_date">` en el form de alta.
   - `app/main.py`: `ui_create_task` suma `priority: Priority = Form(Priority.MEDIA)` y
     `due_date: str = Form("")`, y arma `TaskCreate(..., due_date=due_date or None)`.
   - Tests:
     - El form tiene `media` preseleccionada.
     - `POST /ui/tasks` con `alta` y `2026-12-31` → `303`, y la tarea aparece en `/` con esos datos.
     - `POST /ui/tasks` con `due_date` vacío guarda `due_date` null (chequeado por `GET /tasks`).
     - `POST /ui/tasks` sin mandar `priority` guarda `media`.
   - Commit: `feat(avanzado): cargar prioridad y fecha limite desde el formulario de alta`

9. [ ] **Página: filtros y orden**
   - `app/schemas.py`: `field_validator(mode="before")` en `TaskFilters` que convierte `""` en `None` para
     `priority`, `completed` y `sort_by`.
   - `app/main.py`: `index` recibe `Annotated[TaskFilters, Query()]`, lo pasa a `repo.list_all` y pasa
     `filters` al template.
   - `app/templates/index.html`:
     - `<form method="get" action="/">` con selects de prioridad (todas/alta/media/baja), estado
       (todas/pendientes/completadas) y orden (creación/prioridad/fecha límite), más el checkbox
       "solo vencidas" (`value="true"`).
     - Cada control marca `selected` o `checked` según `filters`.
     - Mensaje "Ninguna tarea coincide con los filtros." si la lista está vacía con algún filtro activo.
   - Tests:
     - `/?priority=alta&completed=false` lista lo mismo que `GET /tasks` con esos parámetros, y los
       controles salen marcados.
     - `/?priority=&completed=&sort_by=` (lo que manda el form en "todas") → `200` con todas las tareas.
     - `/?overdue=true` deja el checkbox marcado.
     - Filtro sin coincidencias → mensaje nuevo y no "No hay tareas todavía.".
     - Base vacía sin filtros → "No hay tareas todavía.".
     - `/?priority=urgente` → `422`.
   - Commit: `feat(avanzado): filtrar y ordenar tareas desde la pagina`

10. [ ] **Documentación de contexto**
    - `CLAUDE.md` (del nivel): reemplazar "Sin tests. Es a propósito" por una línea que diga que hay tests
      en `tests/` y que se corren con `python -m pytest` desde la carpeta.
    - `../CLAUDE.md` (raíz): corregir "Tests (solo existen en `intermedio/`)" y "`inicial/` y `avanzado/` no
      tienen tests" para reflejar que `avanzado/` los tiene.
    - Verificación: releer los dos archivos y confirmar que no queda ninguna afirmación falsa sobre tests
      (`grep -n -i test` en ambos).
    - Commit: `docs: reflejar los tests de avanzado en los CLAUDE.md`

11. [ ] **Verificación final contra el spec**
    - `python -m pytest` completo pasa.
    - El `mtime` de `tasks.db` es el mismo antes y después de correr los tests.
    - Recorrer cada criterio de aceptación del spec y marcar el test que lo cubre. Si alguno no tiene test,
      volver a la task correspondiente.
    - Hacer una copia de respaldo de la `tasks.db` real antes de lo que sigue.
    - Arrancar la app sobre la `tasks.db` real de la demo (esquema viejo): migra sin error y mantiene las tareas.
    - Con la base movida a un costado (no borrada), arrancar sobre una base nueva y revisar a ojo en `/`: seed con prioridades y fechas, la tarea vencida
      marcada, alta con fecha y filtros funcionando.
    - Sin commit, salvo que aparezca algo para corregir (va en su propio commit).

> Regla: si una tarea no se puede verificar por separado, es demasiado grande — partila en dos.
