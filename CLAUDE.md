# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este repo

Material de capacitación ("Curso: IA en el IDE para developers"), no un producto. Son **tres
copias del mismo CRUD de tareas en FastAPI** (`inicial/`, `intermedio/`, `avanzado/`), cada una
congelada en un nivel de madurez distinto para demostrar en vivo una capacidad del IDE.

Consecuencia práctica: **no unifiques, refactorices ni "arregles" código entre niveles**. La
duplicación es intencional, y varias carencias (falta de tests en `inicial`/`intermedio`, endpoints
incompletos, incumplimientos de los estándares) son el material de la demo. Antes de tocar algo que
parezca un descuido, verificá contra el README y las specs si es deliberado.

Todo el material (código, docs, mensajes de error, commits) está **en español**.

## Comandos

Cada nivel es autocontenido y se trabaja **parado dentro de su carpeta** — los imports son
`from app.x import y`, así que el cwd tiene que ser la carpeta del nivel.

```bash
cd avanzado                      # o inicial / intermedio
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload    # API en :8000/docs; avanzado sirve además la web en /
```

Tests (solo existen en `intermedio/`):

```bash
cd intermedio
python -m pytest                      # `python -m` es necesario: no hay pytest.ini
```

`inicial/` y `avanzado/` no tienen tests ni `pytest` en `requirements.txt` — generarlos es parte del
ejercicio, no una omisión a corregir de oficio.

Para volver al estado inicial de una demo: borrar el `tasks.db` del nivel y reiniciar la app
(`init_db()` recrea el esquema y resiembra si la tabla está vacía). Los `.db` están gitignoreados.

## Arquitectura

Misma estructura en los tres niveles, tres capas sin framework de por medio:

- `app/main.py` — handlers FastAPI. Instancia un `TaskRepository` **módulo-global** (`repo = ...`),
  no usa `Depends()` para inyectarlo. Errores siempre como `HTTPException` con
  `status.HTTP_*` y detalle en español (`"Tarea con id {id} no encontrada"`).
- `app/repository.py` — todo el SQL. Abre y cierra una conexión sqlite **por operación**
  (`get_connection()` + `try/finally`); no hay pool ni sesión compartida.
- `app/database.py` — `DB_PATH` (archivo `tasks.db` en la raíz del nivel), `get_connection()`
  e `init_db()`, invocado desde el `lifespan` de FastAPI.
- `app/schemas.py` — Pydantic v2. `TaskCreate` / `TaskUpdate` / `Task` separados; el repositorio
  aplica los updates con `model_copy(update=payload.model_dump(exclude_unset=True))`.

`inicial/` e `intermedio/` tienen el **mismo `app/` byte a byte** (solo difieren los fines de línea
en el working tree). Lo que cambia entre esos dos niveles es lo que los rodea: `intermedio/` suma
`.cursor/skills/`, `.vscode/mcp.json` y `docs/CODING_STANDARDS.md`.

### `avanzado/` — lo que agrega

Es el único nivel con web UI:

- `app/templates/index.html` — página server-rendered (Jinja2). Rutas `/ui/tasks/...` que hacen
  POST y redirigen con `303` a `/`; conviven con la API JSON en `/tasks`.
- `app/database.py` — además del `CREATE TABLE`, corre `_seed_if_empty()` con 5 tareas de fechas
  fijas. Para volver al estado inicial, borrar `tasks.db` y reiniciar la app (la base está
  gitignoreada: `git restore` no la toca).

## Convenciones

De los `.cursorrules` (idénticos en los tres niveles): FastAPI + Pydantic v2, type hints
obligatorios, errores con `HTTPException`, mensajes en español.

`docs/CODING_STANDARDS.md` (en `intermedio/` y `avanzado/`, idénticos) es **el objetivo del
ejercicio de code review, no lo que el código cumple hoy**. El código viola varias de sus reglas a
propósito (repo global en vez de `Depends()`, sin `APIRouter`, sin `/health`, sin paginación,
`HTTPException` repetida, sin docstrings). No apliques esos estándares por tu cuenta: la skill
`code-review-fastapi` (`.cursor/skills/`) está para *reportarlos* en una tabla de severidades y
tiene instrucción explícita de no modificar código salvo pedido expreso.

## Flujo SDD (`avanzado/`)

Los esqueletos reutilizables son `templates/spec.md`, `templates/plan.md` y `templates/tasks.md`
(ojo: `avanzado/templates/` es SDD; las plantillas Jinja de la web viven en `avanzado/app/templates/`).
Se copian y completan por feature, y el resultado va a `specs/`, `plans/` y `tasks/`. Reglas del flujo
que importan al ejecutar: la spec define **qué** y los criterios de aceptación verificables (no el
cómo), el plan se aprueba antes de generar tasks, y cada task es un commit verificable por separado.

## MCP

`.mcp.json` en la raíz define un servidor **qdrant** (deshabilitado para Claude Code en
`.claude/settings.local.json`). Los `.cursor/mcp.json` y `.vscode/mcp.json` de `intermedio/` y
`avanzado/` son **material didáctico** para que los asistentes del curso los copien — el de Cursor
lleva el placeholder literal `TU_TOKEN_AQUI`, que no hay que completar ni reemplazar en el repo.
Ver `README-mcp.md` para el setup (Qdrant vía Docker en `:6333`, GitHub MCP con PAT read-only).

## Fines de línea

`.gitattributes` fuerza `* text=auto eol=lf`. Varios archivos tienen CRLF en el working tree y aun
así `git status` sale limpio. No "normalices" fines de línea ni reescribas archivos enteros por eso.
