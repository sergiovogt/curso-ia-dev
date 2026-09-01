# Tasks — Prioridad y fecha límite en tareas

## Tasks

1. [ ] **Schemas — modelo de lectura y alta:** agregar `Prioridad` (`StrEnum`: `alta`, `media`, `baja`) y campos `prioridad` / `fecha_limite` en `Task` y `TaskCreate` con defaults `media` y `None`.
   - Verificar: `TaskCreate(title="X")` serializa con `prioridad=media` y `fecha_limite=null`; `prioridad="invalida"` o `fecha_limite` no ISO → `ValidationError`.

2. [ ] **Schemas — inmutabilidad en actualización:** dejar `TaskUpdate` sin `prioridad` ni `fecha_limite` y activar `model_config = ConfigDict(extra="forbid")`.
   - Verificar: `TaskUpdate(title="Y", prioridad="alta")` o con `fecha_limite` → `ValidationError` por campo extra.

3. [ ] **DB — esquema para instalaciones nuevas:** extender el `CREATE TABLE` en `database.py` con `prioridad TEXT NOT NULL DEFAULT 'media'` y `fecha_limite TEXT`.
   - Verificar: en una base recién creada, `PRAGMA table_info(tasks)` incluye ambas columnas con el default de `prioridad`.

4. [ ] **DB — migración idempotente:** implementar `_migrate_add_priority_and_due_date(conn)` (check con `PRAGMA table_info` por columna) e invocarla desde `init_db()` antes del seed.
   - Verificar: sobre esquema legacy con las 5 tareas del seed, tras `init_db()` todas quedan con `prioridad=media` y `fecha_limite=null`; una segunda corrida de `init_db()` no falla.

5. [ ] **`app/dates.py`:** crear `today_app() -> date` usando offset fijo UTC-3 (`datetime.now(timezone(timedelta(hours=-3))).date()`).
   - Verificar: el módulo importa y devuelve un `date` (sin depender del TZ del SO para la lógica interna).

6. [ ] **`tests/conftest.py`:** fixture `client` con DB temporal aislada y fixture `freeze_today` que fija `today_app` vía `monkeypatch`.
   - Verificar: `pytest --collect-only tests/` termina sin errores de importación ni de fixtures.

7. [ ] **Tests:** `today_app()` devuelve la fecha UTC-3 correcta ante instantes UTC distintos (`tests/test_dates.py`).
   - Verificar: `pytest tests/test_dates.py` pasa (p. ej. 02:00 UTC vs 15:00 UTC del mismo día calendario).

8. [ ] **Tests:** migración idempotente y defaults en filas legacy del seed (`tests/test_migration.py`).
   - Verificar: `pytest tests/test_migration.py` pasa.

9. [ ] **Repository — persistencia:** actualizar `_row_to_task` y `create` (INSERT) para leer/escribir `prioridad` y `fecha_limite`; `update` y `mark_complete` no modifican esas columnas.
   - Verificar: crear una tarea con `prioridad=alta` y `fecha_limite=2026-07-15` vía repo devuelve esos valores; un `update` de título no altera prioridad ni fecha.

10. [ ] **`app/list_params.py`:** modelo `TaskListParams` con query params `prioridad` (CSV), `fecha_desde`, `fecha_hasta`, `vencidas`, `sin_fecha`, `orden`, `dir` y validaciones (enum, fechas ISO, rangos coherentes).
    - Verificar: params válidos se parsean; valores inválidos (prioridad desconocida, fecha mal formada, `fecha_desde` > `fecha_hasta`) fallan validación.

11. [ ] **Repository — listado filtrado:** implementar `list_filtered(params)` con SQL dinámico parametrizado: filtros de prioridad, rango de fechas (excluyendo `null`), `vencidas` (`fecha_limite < today_app()` y `completed=0`), `sin_fecha`; orden default (prioridad desc + fecha asc, nulls al final) y `orden`/`dir` explícitos con `CASE` para prioridad.
    - Verificar: con datos de prueba en DB, distintos `TaskListParams` devuelven el subconjunto y orden esperados (manualmente o vía asserts que luego cubrirá `test_api_tasks`).

12. [ ] **API — endpoints de listado y alta:** en `main.py`, inyectar `TaskListParams` en `GET /tasks` y reemplazar `list_all()` por `list_filtered(params)`; `POST /tasks` acepta los nuevos campos de `TaskCreate`.
    - Verificar: `POST /tasks` con `{"title":"X"}` → `prioridad=media`, `fecha_limite=null`; `GET /tasks?prioridad=alta` devuelve solo tareas alta.

13. [ ] **Tests:** CRUD ampliado, validaciones 422 en POST, inmutabilidad en `PUT` (422 con `prioridad`/`fecha_limite`), `PATCH /complete` sin alterar campos nuevos, filtros y orden vía `GET /tasks` (`tests/test_api_tasks.py`).
    - Verificar: `pytest tests/test_api_tasks.py` pasa, incluyendo casos de vencidas con `today_app` mockeado en `2026-07-03`.

14. [ ] **UI — handlers:** en `main.py`, `GET /` usa `TaskListParams` (helper compartido desde `request.query_params`), pasa `today=today_app()` y estado de filtros al template; `POST /ui/tasks` recibe prioridad y fecha límite por `Form`.
    - Verificar: la página carga con filtros en la URL; enviar el formulario de alta con prioridad/fecha persiste los valores (comprobable vía `GET /tasks`).

15. [ ] **UI — template:** en `index.html`, agregar select de prioridad e input `type=date` en el alta; bloque de filtros/orden con `method="get"`; mostrar prioridad, fecha límite (o «Sin fecha límite») y badge/clase vencida; estilos mínimos para prioridades y estado vencida; sin controles de edición post-creación.
    - Verificar: el HTML renderizado incluye los controles; una tarea pendiente con `fecha_limite` anterior a `today_app()` muestra el indicador vencida; una completada con fecha pasada no.

16. [ ] **Tests:** formulario de alta, filtros reflejados en URL, badge vencida según `completed` y fecha vs `today_app` mockeado, ausencia de edición post-creación (`tests/test_ui.py`).
    - Verificar: `pytest tests/test_ui.py` pasa.

17. [ ] **Correr la suite completa** y verificar contra los criterios de aceptación del spec (`avanzado/specs/prioridad-fecha-limite.md`).
    - Verificar: `pytest tests/` pasa sin fallos.
