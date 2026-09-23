# CLAUDE.md — nivel avanzado

Contexto del proyecto para el agente. Se carga en todas las sesiones que se
abran parado en esta carpeta, así que conviene que sea corto y que todo lo que
diga sea cierto.

## Stack

- **FastAPI + Pydantic v2**, Python 3.12+.
- Persistencia en SQLite vía `app/database.py`; el acceso a datos vive en
  `app/repository.py`.
- **Página web server-rendered** con Jinja2 en `app/templates/index.html`.
- La base arranca sembrada con tareas de ejemplo.
- Dos capas de tests: pytest en `tests/` y E2E con Playwright en `e2e/`.
  Ver [Tests](#tests).

## Tests

**Pytest no alcanza para lo que toca la página.** Son dos capas y cubren cosas
distintas; una feature de front no está testeada hasta que pasó por las dos.

- **`tests/` (pytest)** — API JSON, repositorio y base. Corren sobre una base
  temporal, no tocan `tasks.db`:

  ```bash
  python -m pytest
  ```

  Parado en esta carpeta, con `python -m` (no hay `pytest.ini`).

- **`e2e/` (Playwright)** — todo lo que sea comportamiento de la página: filtros,
  orden, marcas visuales, formularios, redirects. Requiere la app levantada
  aparte en el **8010** (`uvicorn app.main:app --port 8010 --reload`; el 8000
  suele estar tomado por Docker):

  ```bash
  cd e2e && npx playwright test
  ```

  La config está en `headless: false` **a propósito**: en la capacitación el
  punto es que se vea el navegador abriéndose. No la pases a headless para que
  "corra más rápido".

Por qué la distinción importa: `tests/test_web.py` verifica el HTML **como
string**, con `TestClient` y expresiones regulares. Confirma que el markup trae
`class="overdue"` o `Prioridad: alta`, pero nunca renderiza CSS ni ejecuta un
navegador. Un estilo que no se aplica, un botón que desborda su contenedor, un
form que no envía o un `303` que deja la página en un estado raro pasan esos
tests sin problema. Para eso está `e2e/`.

Regla práctica: si el cambio toca `app/templates/`, los handlers `/ui/` o el
render de `/`, sumá o corré el test de Playwright correspondiente —y miralo
abrirse— antes de darlo por terminado. No declares verificada una feature de
front apoyándote solo en la salida de pytest.

## Convenciones

- **Type hints obligatorios** en parámetros y retorno.
- Los errores se devuelven con `HTTPException`, nunca con returns de error.
- **Los mensajes de error van en español.** Recurso no encontrado:
  `"Tarea con id {id} no encontrada"`.
- `status.HTTP_*` en lugar de números mágicos.

Las convenciones completas —las que usa la skill de review— están en
[`docs/CODING_STANDARDS.md`](docs/CODING_STANDARDS.md). Este archivo es el
resumen; ante una diferencia, manda el de `docs/`.

## Qué hay en esta carpeta

| Ruta | Qué es |
|---|---|
| `.claude/skills/code-review-fastapi/` | Skill de review del proyecto, con sus ejemplos |
| `.mcp.json` | Servidores MCP del nivel: GitHub y Qdrant |
| `docs/CODING_STANDARDS.md` | La referencia que evalúa la skill |
| `tests/` | Tests de pytest: API, repositorio y base |
| `e2e/` | Tests E2E con Playwright: la página en un navegador real |
| `templates/` | `spec.md`, `plan.md`, `tasks.md` |
| `README-mcp.md` | Cómo levantar los MCP |

El token de GitHub **no va en `.mcp.json`**: se lee de la variable de entorno
`GITHUB_PERSONAL_ACCESS_TOKEN`. Ver `README-mcp.md`.
