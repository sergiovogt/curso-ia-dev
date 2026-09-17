# Plan técnico — Prioridad y fecha límite en tareas

Implementa [`specs/prioridad-y-fecha-limite.md`](../specs/prioridad-y-fecha-limite.md).

## Decisiones técnicas

| Decisión | Opción elegida | Por qué / qué se descarta |
|---|---|---|
| Tipo de `priority` | `Priority(StrEnum)` en `schemas.py` con `ALTA="alta"`, `MEDIA="media"`, `BAJA="baja"` | Pydantic lo valida (`422` para `"urgente"`), OpenAPI muestra los valores posibles y el repo compara contra el enum, no contra strings sueltos. Se descarta `Literal[...]`: no deja nombrar el tipo para reusarlo en form, filtros y template. |
| Tipo de `due_date` | `datetime.date` | Pydantic ya rechaza `"31/12/2026"` y `"2026-12-31T10:00:00"` (verificado con la versión instalada, 2.13). Se descarta un validador propio por regex: duplica lo que Pydantic ya hace. Ver riesgo sobre medianoche y timestamps. |
| `priority` null en `POST` | Campo `priority: Priority = Priority.MEDIA` | Un tipo no opcional rechaza `null` con `422` y aplica el default cuando no viene el campo. |
| `priority` null en `PUT` | `priority: Priority \| None = None` más `field_validator` que rechaza `None` explícito con mensaje en español | Hace falta `None` como default para distinguir "no vino" (lo resuelve `exclude_unset`) de "vino null". El validador solo corre cuando el campo llega en el body, así que no rompe los updates parciales. Se descarta tipar `priority: Priority = None`: funciona, pero el type hint miente. |
| `due_date` null en `PUT` | `due_date: date \| None = None`, sin validador | `exclude_unset=True` ya incluye un `null` explícito en el update, así que la fecha se borra sin código extra. |
| Almacenamiento | Columnas `priority TEXT NOT NULL DEFAULT 'media'` y `due_date TEXT` (ISO `YYYY-MM-DD`) | Igual que `created_at`, que ya es texto ISO. Las fechas ISO se ordenan bien como texto, así que el `ORDER BY` y el `<` de vencidas funcionan en SQL. Se descarta un `CHECK` sobre `priority`: todo lo que escribe pasa por modelos validados y agregarlo por `ALTER TABLE` complica la migración sin ganancia para la demo. |
| Migración de bases existentes | En `init_db()`: `CREATE TABLE IF NOT EXISTS` con el esquema completo y después `_migrate(conn)`, que lee `PRAGMA table_info(tasks)` y hace `ALTER TABLE ... ADD COLUMN` solo para las columnas que faltan. Corre antes del seed. | Idempotente por construcción: en el segundo arranque no hay nada que agregar. No hace falta llevar la cuenta de versiones (`PRAGMA user_version`) para dos columnas. El `DEFAULT 'media'` de la columna completa las filas viejas en el mismo `ALTER`. Se descarta pedir que se borre `tasks.db`: el spec exige conservar las tareas. |
| Contrato de filtros | Un modelo `TaskFilters` en `schemas.py` (`priority: Priority \| None`, `completed: bool \| None`, `overdue: bool = False`, `sort_by: SortBy \| None`) recibido con `Annotated[TaskFilters, Query()]` | Un solo modelo para `GET /tasks` y para `GET /`: la página y la API validan y filtran con el mismo código, que es lo que pide el criterio "el listado muestra el mismo resultado que `GET /tasks`". FastAPI soporta modelos como query params desde 0.115 (el piso de `requirements.txt`; verificado con la 0.116 instalada). Se descarta repetir los cuatro `Query()` en cada handler. |
| Opciones "todas" del form de la página | `field_validator(mode="before")` en `TaskFilters` que convierte `""` en `None` para `priority`, `completed` y `sort_by` | Un `<select>` en "todas" manda `priority=` vacío, y sin esto la página devuelve `422` al aplicar los filtros. Se descarta JavaScript para no mandar campos vacíos: el spec deja afuera el JS. Efecto secundario: `GET /tasks?priority=` devuelve todo en lugar de `422` (el spec no lo cubre). |
| Orden de enums en SQL | `SortBy(StrEnum)` con `PRIORITY="priority"` y `DUE_DATE="due_date"`, y un dict en el repo que mapea cada valor a un fragmento fijo de `ORDER BY` | El input del usuario nunca se interpola en el SQL: solo elige una clave de un dict cerrado. Orden por prioridad: `CASE priority WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END, id`. Por fecha: `due_date IS NULL, due_date, id` (las tareas sin fecha van al final). Sin `sort_by`: `id`, como hoy. |
| Filtros en el repo | `list_all(filters: TaskFilters \| None = None)` arma el `WHERE` con condiciones y parámetros `?` | Sigue siendo el único método de listado y los llamadores sin filtros no cambian. Se descarta ordenar o filtrar en Python: el repo ya concentra todo el SQL. |
| "Hoy" para vencidas | `date.today()` en Python, pasado como parámetro: `completed = 0 AND due_date IS NOT NULL AND due_date < ?` | El spec dice "fecha local del servidor". Se descarta `date('now')` de SQLite porque usa UTC y cerca de la medianoche daría otro día. |
| Marca de vencida en la página | `@property is_overdue` en el modelo `Task` (no completada, con fecha y fecha `< date.today()`) | El template lo usa como `t.is_overdue`. Una `@property` común no se serializa, así que la respuesta JSON no suma campos que el spec no pidió. Se descarta `@computed_field`, que sí aparecería en la API, y también calcularlo en Jinja: sería una tercera copia de la regla. |
| Mensaje "sin coincidencias" | El handler de `/` pasa `filters` al template; si la lista está vacía y hay algún filtro activo (`priority`, `completed` u `overdue`; `sort_by` no cuenta) se muestra "Ninguna tarea coincide con los filtros." | No hace falta una segunda consulta para contar el total. Ver riesgo con base vacía. |
| Alta desde la página | `ui_create_task` recibe `priority: Priority = Form(Priority.MEDIA)` y `due_date: str = Form("")`, y arma `TaskCreate(..., due_date=due_date or None)` | Un `<input type="date">` vacío manda `""`, y `date` rechaza `""` (verificado). Es el mismo patrón que ya usa `description or None`. |
| Herramienta de tests | `pytest` + `TestClient` de FastAPI, con `httpx2` como cliente HTTP (mismas versiones que `intermedio/requirements.txt`) | Es el mismo stack que ya usa `intermedio/`, así que el curso no suma un patrón nuevo. Con `httpx2`, Starlette no emite el `DeprecationWarning` de `httpx`. Se descarta testear el repo directo sin HTTP: los criterios del spec están escritos sobre la API y la página. |
| Aislamiento de la base en tests | Fixture `client` en `tests/conftest.py`: `monkeypatch.setattr("app.database.DB_PATH", tmp_path / "test.db")` y `with TestClient(app)` (así corre el `lifespan` y con él `init_db()`), y después `DELETE FROM tasks` | `get_connection()` lee `DB_PATH` en cada llamada, así que alcanza con redirigir la ruta; es el mismo fixture de `intermedio/`. El `DELETE` saca el seed para que cada test controle exactamente qué tareas hay. Un segundo fixture, `seeded_client`, no borra nada y se usa solo en los tests del seed. |
| Fechas en los tests de vencidas | Fechas relativas: `date.today() - timedelta(days=1)`, `date.today()` y `date.today() + timedelta(days=1)` | Los tests pasan corran el día que corran, sin congelar el reloj. Se descarta agregar `freezegun` o inyectar un reloj en la app: sería una dependencia más o un cambio de diseño solo para testear, y con fechas relativas alcanza. Los tests del seed no chequean "vencida" contra hoy (ver riesgos). |
| Test de migración | Crear a mano un `.db` en `tmp_path` con el `CREATE TABLE` viejo y dos filas, apuntar `DB_PATH` ahí, llamar `init_db()` dos veces y leer las filas | Prueba el caso real (una base anterior a la feature) sin depender de un archivo binario versionado. El esquema viejo se copia literal en el test y no se importa del código, porque el código ya va a tener el esquema nuevo. |
| Asserts sobre la página | Buscar substrings en `response.text` (por ejemplo `'value="alta" selected'`, `class="overdue"`, el texto del mensaje) | Alcanza para los criterios y no suma un parser HTML como dependencia. Esto ata los tests al markup exacto del template; ver riesgos. |
| Tests por task | Cada task del plan trae los tests de lo que implementa, en el mismo commit | Encaja con la regla SDD de que cada task es un commit verificable: el commit se verifica corriendo `python -m pytest`. |
| Estándares de `docs/CODING_STANDARDS.md` | No se aplican (`Depends()`, `APIRouter`, docstrings, paginación, helper de `404`) | Están fuera de alcance según el spec, y el incumplimiento es material del ejercicio de code review. El código nuevo sigue el estilo del archivo donde se escribe. |

## Archivos afectados

- `app/schemas.py`:
  - Agrega `Priority(StrEnum)` y `SortBy(StrEnum)`.
  - Agrega `priority` y `due_date` a `TaskCreate`, `TaskUpdate` (con el validador de null) y `Task` (con la property `is_overdue`).
  - Agrega el modelo `TaskFilters` con su validador de strings vacíos.
- `app/database.py`:
  - Suma `priority` y `due_date` al `CREATE TABLE`.
  - Nueva función `_migrate(conn)`, llamada entre el `CREATE` y `_seed_if_empty`.
  - `_SEED_TASKS` pasa a tuplas de 6 elementos y el `INSERT` del seed suma las dos columnas.
  - Valores del seed (fechas fijas):

    | # | Tarea | Completada | Prioridad | Fecha límite | Para qué |
    |---|---|---|---|---|---|
    | 1 | Configurar el pipeline de CI | sí | alta | 2026-06-10 | Completada con fecha pasada: no se marca vencida |
    | 2 | Migrar el login a OAuth | no | alta | 2026-07-01 | Pendiente vencida |
    | 3 | Escribir la doc del endpoint de pagos | no | baja | — | Sin fecha |
    | 4 | Revisar el PR de checkout | no | media | 2027-12-15 | Pendiente con fecha futura |
    | 5 | Actualizar dependencias de FastAPI | sí | media | — | Completa las tres prioridades |

- `app/repository.py`:
  - `_row_to_task` lee las dos columnas nuevas (`date.fromisoformat` si `due_date` no es null).
  - `create` y `update` escriben las dos columnas.
  - `list_all` recibe `TaskFilters` y arma `WHERE` y `ORDER BY`.
  - `mark_complete`, `get_by_id` y `delete` no cambian (salvo que heredan el `_row_to_task` nuevo).
- `app/main.py`:
  - `list_tasks` e `index` reciben `Annotated[TaskFilters, Query()]` y lo pasan a `repo.list_all`.
  - `index` también pasa `filters` al template.
  - `ui_create_task` suma los campos `priority` y `due_date` del form.
  - El resto de los handlers no cambia.
- `app/templates/index.html`:
  - El form de alta suma un `<select name="priority">` con `media` preseleccionada y un `<input type="date" name="due_date">`.
  - Nuevo `<form method="get" action="/">`:
    - Selects `priority` y `completed`, y `sort_by`, cada uno con una opción vacía para "todas" o "creación".
    - Checkbox `overdue` con `value="true"`.
    - Cada control marca `selected`/`checked` según `filters`.
  - Cada `<li>` suma la clase `overdue` si `t.is_overdue` y muestra en `.meta` la prioridad y "Vence: YYYY-MM-DD" si tiene fecha.
  - Nuevos estilos para `.overdue` y para la etiqueta de prioridad.
  - Nuevo mensaje de "sin coincidencias".
- `requirements.txt` — suma `pytest>=8.3.0` y `httpx2>=2.12.0`, con el mismo comentario que en `intermedio/`.
- `tests/conftest.py` (nuevo) — fixtures `client` (base temporal y vacía) y `seeded_client` (base temporal con el seed).
- `tests/test_api_tasks.py` (nuevo) — tests de las secciones "Modelo y API", "API — filtros" y "API — orden" del spec.
- `tests/test_web.py` (nuevo) — tests de la sección "Página web".
- `tests/test_database.py` (nuevo) — migración desde el esquema viejo, dos arranques seguidos y contenido del seed.
- `CLAUDE.md` (del nivel) — la línea "Sin tests. Es a propósito" deja de ser cierta: pasa a decir que hay tests y que se corren con `python -m pytest` desde la carpeta.
- `../CLAUDE.md` (raíz) — "Tests (solo existen en `intermedio/`)" y "`inicial/` y `avanzado/` no tienen tests" dejan de ser ciertas en `avanzado/`: se actualizan.

## Riesgos

- **Sumar tests a `avanzado/` cambia el material del curso**: hoy el `CLAUDE.md` raíz dice que generar tests para `avanzado/` "es parte del ejercicio" → si alguna sesión usa `avanzado/` sin tests como punto de partida, esa demo tiene que arrancar desde un commit anterior a esta feature. Se actualizan los dos `CLAUDE.md` para que no mientan.
- **La migración corre sobre una base con datos reales de la demo** → `ADD COLUMN` en SQLite no reescribe ni borra filas, y `_migrate` solo agrega columnas que faltan. Lo cubre `tests/test_database.py`: una base con el esquema viejo conserva sus filas (en `media` y sin fecha) y aguanta dos arranques seguidos. Como chequeo extra, conviene arrancar la app una vez sobre la `tasks.db` real de la demo.
- **Los tests podrían tocar el `tasks.db` de la demo** si algún test abre conexiones sin pasar por el fixture → toda la app lee `DB_PATH` a través de `get_connection()`, y los tests nunca usan la app sin el fixture. Verificación: comparar el `mtime` de `tasks.db` antes y después de `python -m pytest`.
- **Tests de vencidas que fallan cerca de medianoche**: el test calcula `date.today()` y la app vuelve a calcularlo en el request; si justo cambia el día en el medio, el resultado difiere → es una ventana de milisegundos y se acepta. No se congela el reloj (ver decisiones).
- **El seed usa fechas fijas y los tests corren en cualquier fecha** → los tests del seed comparan los valores guardados contra la tabla de arriba (prioridad, completada y fecha literal de cada tarea) y no los comparan contra hoy ni llaman a `?overdue=true` sobre el seed. Cuando la tarea 4 (2027-12-15) venza, un test así se rompería solo.
- **Tests de la página atados al markup**: un cambio cosmético en `index.html` (orden de atributos, comillas) rompe asserts por substring → los asserts buscan fragmentos cortos y estables (`value="alta" selected`, la clase `overdue`, textos visibles), y el template los escribe siempre con el mismo formato.
- **El seed nuevo no se ve en una base ya sembrada** (`_seed_if_empty` no toca una tabla con filas, y la migración deja todo en `media` sin fecha) → es el comportamiento esperado. Para ver el seed nuevo hay que borrar `tasks.db` y reiniciar, como ya documenta el `CLAUDE.md` raíz.
- **La tarea con fecha futura del seed va a vencer** (fecha fija 2027-12-15) → aceptado por el spec (fechas fijas y reproducibles). Queda más de un año de margen; si hace falta, se corre la fecha en el seed.
- **Pydantic acepta más formatos de fecha de lo que sugiere el spec**:
  - `"2026-12-31T00:00:00"` y timestamps enteros que caen justo a medianoche se convierten a fecha en lugar de dar `422` (verificado).
  - El spec solo exige rechazar fecha con hora distinta de cero y el formato `dd/mm/yyyy`, así que se acepta.
  - Si se quisiera cerrar, la opción es `Field(strict=True)`, que conviene decidir antes de las tasks.
- **`priority=` vacío deja de dar `422`** por el validador que necesita el form → no rompe ningún criterio. Queda documentado en la tabla de decisiones.
- **Dos copias de la regla "vencida"** (SQL en `list_all` y `Task.is_overdue`) pueden divergir → las dos usan `date.today()` y la misma comparación estricta `<`. Los tests crean el mismo juego de tareas (vencida, vence hoy, futura, sin fecha, completada con fecha pasada) y chequean que `GET /tasks?overdue=true` y las `<li class="overdue">` de la página marcan exactamente las mismas.
- **`GET /tasks` y `GET /` cambian de firma** → sin parámetros el resultado es idéntico a hoy (`ORDER BY id`). Las rutas `/ui/.../complete` y `/ui/.../delete` redirigen a `/` sin query string, así que después de completar o borrar se pierden los filtros aplicados. El spec solo pide que "sigan funcionando como hoy", así que se acepta.
- **Mensaje de "sin coincidencias" con base vacía y filtros activos** → muestra "Ninguna tarea coincide..." en lugar de "No hay tareas todavía.". El spec solo define el caso "hay tareas pero ninguna coincide", así que se acepta para evitar una segunda consulta.
- **Los `422` de validación salen en inglés** (mensajes por defecto de Pydantic y FastAPI), y en la página se ven como JSON crudo → igual que hoy con el resto de las validaciones. Solo el mensaje propio del validador de null va en español.
- **Bug existente fuera de alcance**: `PUT /tasks/{id}` con `"title": null` o `"completed": null` hoy termina en un `500` (viola `NOT NULL`) → no se corrige en esta feature para no mezclar cambios. Solo se evita repetirlo en `priority`.
- **Orden de `ALTER` y seed**: si el seed corriera antes de `_migrate` sobre una base vieja vacía, el `INSERT` fallaría por columnas inexistentes → `_migrate` va siempre antes que `_seed_if_empty`.
