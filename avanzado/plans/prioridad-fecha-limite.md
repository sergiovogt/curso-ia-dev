# Plan técnico — Prioridad y fecha límite en tareas

## Decisiones técnicas

| Decisión | Opción elegida | Por qué / qué se descarta |
|---|---|---|
| Tipo de prioridad | `StrEnum` (`Prioridad`: `alta`, `media`, `baja`) en `schemas.py` | Valores cerrados alineados al spec; validación automática en Pydantic. Descartado: `int` o strings sueltos (menos expresivo en OpenAPI). |
| Almacenamiento de `fecha_limite` | Columna SQLite `TEXT` con formato `YYYY-MM-DD`; en Python `date \| None` | Coincide con el spec (solo fecha, sin hora). Descartado: `DATETIME` (sobra complejidad y no está en alcance). |
| Migración de esquema | `ALTER TABLE` idempotente en `init_db()` al arranque | La app no tiene framework de migraciones; el seed y las bases demo ya existen sin las columnas. `ADD COLUMN prioridad TEXT NOT NULL DEFAULT 'media'` y `ADD COLUMN fecha_limite TEXT` cubren filas existentes sin script aparte. Descartado: recrear tabla o migración manual documentada (más fricción en la demo). |
| Inmutabilidad post-creación | `TaskUpdate` **sin** `prioridad`/`fecha_limite` + `model_config = ConfigDict(extra="forbid")` | El spec exige **422** si el body incluye esos campos; con `extra="forbid"` Pydantic rechaza automáticamente. Descartado: validación manual en el handler (duplica lógica) o ignorar campos extra (incumple el spec). |
| Filtro y orden | Modelo `TaskListParams` (Pydantic) + método `TaskRepository.list_filtered(params)` | Un solo lugar para reglas de listado compartidas por `GET /` y `GET /tasks`. Descartado: filtrar en Python sobre `list_all()` (no escala, mezcla capas) o duplicar SQL en dos handlers. |
| Construcción de SQL dinámico | Cláusulas `WHERE`/`ORDER BY` parametrizadas en el repositorio | SQLite no tiene enums nativos; `IN (?, ?, ?)` evita inyección. Descartado: ORM (no existe en el proyecto). |
| Orden por prioridad | `CASE prioridad WHEN 'alta' THEN 3 … END` | Orden semántico estable independiente del orden alfabético. Descartado: `ORDER BY prioridad` lexicográfico (`alta` < `baja` < `media`). |
| Nulls en orden por fecha | `ORDER BY fecha_limite IS NULL, fecha_limite {dir}` | Cumple el spec: sin fecha siempre al final. Descartado: tratar `NULL` como fecha lejana en SQL (comportamiento distinto según dirección). |
| Criterio «hoy» | Función `today_app()` en `app/dates.py`: fecha calendario en **UTC-3** (`datetime.now(timezone(timedelta(hours=-3))).date()`) | Equivalente a «hoy» fijo en UTC-3, independiente del TZ del SO donde corre el servidor. Descartado: `date.today()` naive (depende del SO, no es UTC-3 en máquinas con otro huso). |
| Criterio «vencidas» | `fecha_limite < today_app()` **y** `completed = 0` | Usa el mismo «hoy» que el badge vencida en UI y el filtro `?vencidas=1`. Descartado: UTC puro o TZ del servidor sin fijar offset. |
| UI de filtros | Formulario `GET /` con query params iguales a la API | La URL es la fuente de verdad; la página y `GET /tasks` comparten contrato. Descartado: filtrado solo en cliente con JS (no server-rendered, duplica reglas). |
| Estado vencida en UI | Clase CSS + badge en Jinja (`not t.completed and t.fecha_limite and t.fecha_limite < today`), con `today = today_app()` | Misma función que el filtro `vencidas`. Descartado: lógica solo en CSS (no puede evaluar fecha). |
| Redirects POST UI | Mantener redirect a `/` sin query string | Fuera de alcance del spec. Tras completar/borrar se pierden filtros activos (riesgo menor documentado abajo). |

## Archivos afectados

- `app/schemas.py` — Agregar `Prioridad` (`StrEnum`), campos `prioridad` y `fecha_limite` en `Task`/`TaskCreate`; defaults (`media`, `None`); **no** agregar esos campos a `TaskUpdate`; activar `extra="forbid"` en `TaskUpdate`.
- `app/database.py` — Extender `CREATE TABLE` para instalaciones nuevas; función `_migrate_add_priority_and_due_date(conn)` con `ALTER TABLE` condicional (comprobar columnas vía `PRAGMA table_info`); invocarla desde `init_db()` antes del seed.
- `app/dates.py` *(nuevo)* — `today_app() -> date` con offset fijo UTC-3; único punto de verdad para «hoy» en repo, handlers y tests.
- `app/list_params.py` *(nuevo)* — Modelo `TaskListParams` con query params: `prioridad` (lista, parseo de CSV), `fecha_desde`, `fecha_hasta`, `vencidas`, `sin_fecha`, `orden`, `dir`; validaciones (fechas ISO, valores de enum, rangos coherentes).
- `app/repository.py` — Actualizar `_row_to_task`, `create` e `INSERT`; reemplazar uso de `list_all()` por `list_filtered(params)`; SQL dinámico para filtros y orden (filtro `vencidas` usa `today_app()`); `update`/`mark_complete` sin tocar columnas nuevas.
- `app/main.py` — Inyectar `TaskListParams` en `GET /` y `GET /tasks`; pasar `today` y estado de filtros al template; ampliar `ui_create_task` con `Form` de prioridad y fecha; rechazo 422 en `PUT` ya cubierto por schema; helper compartido para parsear params desde `request.query_params` en la ruta HTML.
- `app/templates/index.html` — Campos de alta (select prioridad, `input type=date`); bloque de filtros/orden (`method="get"`); mostrar prioridad, fecha límite y badge vencida; estilos mínimos para prioridades y estado vencida.
- `tests/conftest.py` — Fixture `client` con DB temporal en memoria/archivo tmp; fixture `freeze_today` que fija `today_app()` vía `monkeypatch` para tests deterministas de vencidas.
- `tests/test_migration.py` — Migración idempotente sobre esquema legacy (5 tareas seed → `prioridad=media`, `fecha_limite=null`); segunda corrida de `init_db()` sin error.
- `tests/test_api_tasks.py` — CRUD ampliado, validaciones 422, inmutabilidad en `PUT`, filtros/orden vía `GET /tasks` (prioridad CSV, rango, `vencidas`, `sin_fecha`, orden default y explícito).
- `tests/test_dates.py` *(nuevo)* — `today_app()` devuelve la fecha UTC-3 correcta ante distintos instantes UTC (p. ej. 02:00 UTC del día D → D−1 en UTC-3 si aplica, o 15:00 UTC → D en UTC-3).
- `tests/test_ui.py` — Formulario de alta con prioridad/fecha; controles de filtro en HTML; badge vencida presente/ausente según `completed` y fecha vs `today_app()` mockeado.

## Tests

Cobertura mapeada a criterios del spec (`avanzado/specs/prioridad-fecha-limite.md`):

| Archivo | Qué verifica |
|---|---|
| `tests/test_migration.py` | Modelo y migración: columnas nuevas, defaults en filas existentes, idempotencia. |
| `tests/test_dates.py` | «Hoy» = fecha en UTC-3, no TZ del SO ni UTC naive. |
| `tests/test_api_tasks.py` | POST defaults y 422; PUT inmutable (422 con `prioridad`/`fecha_limite`); PATCH complete sin cambiar campos nuevos; filtros `prioridad`, `fecha_desde`/`fecha_hasta`, `vencidas=1`, `sin_fecha=1`, combinados; orden default y `orden`+`dir`. |
| `tests/test_ui.py` | Campos en formulario de alta; filtros/orden reflejados en URL; badge vencida solo en no completadas con `fecha_limite < today_app()`; sin controles de edición post-creación. |

**Estrategia:** pytest + `TestClient` de FastAPI; DB aislada por test en tmp; `monkeypatch` sobre `app.dates.today_app` (no freezegun extra) para escenarios de vencidas con fecha fija conocida en UTC-3.

**Casos mínimos de vencidas (con `today_app()` fijado en `2026-07-03`):**

- Tarea pendiente `fecha_limite=2026-07-02` → incluida en `?vencidas=1` y badge en UI.
- Tarea pendiente `fecha_limite=2026-07-03` → **no** vencida (límite es hoy).
- Tarea completada `fecha_limite=2026-07-02` → excluida de `?vencidas=1` y sin badge.

## Orden de implementación sugerido

1. **Schemas + migración DB** — Base del contrato y datos existentes con `media`/`null`.
2. **`app/dates.py` + `tests/test_dates.py`** — Contrato de «hoy» UTC-3 antes de filtros vencidas.
3. **Repository** — Persistencia en `create` y `list_filtered` con todos los criterios del spec.
4. **API + `tests/test_api_tasks.py` y `tests/test_migration.py`** — Endpoints y migración verificados.
5. **UI + `tests/test_ui.py`** — Formulario de alta, filtros GET, visualización y estilos vencida.
6. **Correr suite completa** — `pytest tests/` contra criterios de aceptación del spec.

## Riesgos

- **Migración no idempotente** → Si `ALTER TABLE` corre dos veces falla. Mitigación: comprobar existencia de columnas con `PRAGMA table_info(tasks)` antes de cada `ADD COLUMN`.
- **Bases con esquema parcialmente migrado** → Columna `prioridad` sin `fecha_limite` o viceversa. Mitigación: migrar cada columna por separado con su propio check; defaults explícitos en `ADD COLUMN`.
- **`PUT` con campos extra no rechazados** → Pydantic v2 ignora extras por defecto. Mitigación: `extra="forbid"` en `TaskUpdate` (decisión clave del plan).
- **Desfase UI ↔ API en query params** → Listado HTML distinto al JSON con mismos filtros. Mitigación: un solo modelo `TaskListParams` usado en ambos endpoints; template genera la misma query string.
- **Orden de prioridad incorrecto en SQL** → `ORDER BY prioridad` alfabético no cumple el spec. Mitigación: expresión `CASE` documentada y probada con datos de ejemplo.
- **`NULL` en rango de fechas** → Tareas sin fecha aparecen en filtros de rango. Mitigación: condición `fecha_limite IS NOT NULL` implícita en `fecha_desde`/`fecha_hasta`.
- **Pérdida de filtros tras POST** (`/complete`, `/delete`, alta) → Redirect a `/` limpia query params. Mitigación: aceptable según alcance; mejora futura opcional propagando `request.url.query` en el redirect.
- **Regresión en endpoints existentes** — Clientes que envían JSON desconocido en `PUT`. Mitigación: `extra="forbid"` solo aplica a campos no definidos; si hoy ya envían campos extra silenciosos, pasarán a 422 (comportamiento más estricto, deseable).
- **Desfase TZ del SO vs UTC-3** → Vencidas distintas si se usara `date.today()` en un servidor UTC. Mitigación: `today_app()` centralizado; tests con `monkeypatch` fijan la fecha; no depender del reloj real en CI.
- **Tests flaky por hora del día** → Casos en el límite medianoche UTC-3 fallan según cuándo corren. Mitigación: siempre mockear `today_app()` en tests de vencidas/UI; `test_dates.py` usa instantes UTC explícitos sin reloj del sistema.
