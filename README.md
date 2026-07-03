# Curso: IA en el IDE para developers

Material de capacitación para equipos de desarrollo sobre cómo trabajar con
modelos de IA en el editor (Cursor y GitHub Copilot): cómo piensan los modelos,
cómo controlar el contexto y cómo usar las herramientas del IDE de forma efectiva.

El curso está organizado en tres niveles progresivos, cada uno con su proyecto
de práctica sobre el **mismo CRUD de tareas en FastAPI**, que va ganando
madurez a medida que se sube de nivel.

## Estructura del repo

```
.
├── inicial/         # Nivel 1 — fundamentos: prompting, contexto y tokens
│   ├── app/         # CRUD de tareas (FastAPI)
│   ├── docs/        # cheatsheet, buenas prácticas y slides
│   └── requirements.txt
├── intermedio/      # Nivel 2 — skills del proyecto + MCP
│   ├── app/
│   ├── .cursor/     # skills reutilizables + configuración de MCP
│   ├── docs/        # CODING_STANDARDS.md
│   └── README-mcp.md
└── avanzado/        # Nivel 3 — Spec-Driven Development (SDD)
    ├── app/         # el mismo CRUD, ahora con página web (Jinja2)
    ├── templates/   # esqueletos de spec / plan / tasks
    └── requirements.txt
```

### Requisitos

- Python 3.12+

Cada nivel es autocontenido: se trabaja parado dentro de su carpeta, con su
propio `requirements.txt`.

## Nivel inicial — fundamentos

Un **CRUD de tareas** en FastAPI, deliberadamente simple y con "huecos" (sin
tests, endpoints faltantes) para demostrar en vivo las funcionalidades del IDE:
autocompletado, edición inline, chat con contexto, reglas del proyecto y
generación de tests.

```bash
cd inicial
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API en `http://127.0.0.1:8000` y documentación interactiva en `/docs`.

**Documentación** (`inicial/docs/`):
- `cheatsheet-cursor.md` — comandos y atajos de Cursor en una hoja (Windows).
- `buenas-practicas-tokens.md` — optimización de contexto y tokens.
- `Capacitacion_1_Slides.pptx` — slides de la primera sesión.

## Nivel intermedio — skills + MCP

El mismo CRUD, esta vez para practicar cómo **extender el IDE**: dar contexto a
nivel de codebase con *skills* reutilizables y a nivel de herramientas con
servidores *MCP*.

- `.cursor/skills/code-review-fastapi/` — una skill de code review sobre el
  proyecto, con sus ejemplos.
- `.cursor/mcp.json` — configuración de un servidor MCP.
- `docs/CODING_STANDARDS.md` — estándares que las skills toman como referencia.
- `README-mcp.md` — cómo levantar y usar el MCP en este nivel.

Puesta en marcha idéntica al nivel inicial (`cd intermedio`, venv, `pip install`,
`uvicorn app.main:app --reload`).

## Nivel avanzado — Spec-Driven Development

El mismo CRUD, ahora con **página web** (server-rendered con Jinja2) y sembrado
con tareas de ejemplo. Es la base para practicar el flujo **spec → plan →
tasks**: en vez de pedirle a la IA que construya algo directo, se define primero
*qué* hay que construir y *qué significa que está terminado*, con revisión
humana en cada paso.

```bash
cd avanzado
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La página queda en `http://127.0.0.1:8000/` y la API JSON en `/tasks` (+ `/docs`).

- `templates/spec.md`, `plan.md`, `tasks.md` — esqueletos reutilizables de los
  tres artefactos de SDD. Se copian y se completan para cada feature nueva.

### Ramas de la demo (SDD)

El flujo se demuestra construyendo la misma feature de dos formas sobre esta base:

- **`main`** — estado inicial: el CRUD con web UI, sin la feature.
- **`demo-a-congelada`** — la feature hecha con *vibe coding* (un pedido directo,
  sin spec): sirve para ver las decisiones que la IA toma sola.
- **`demo-b-referencia`** — la misma feature con el flujo SDD completo (spec →
  plan → tasks) y su suite de tests.
