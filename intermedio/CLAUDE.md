# CLAUDE.md — nivel intermedio

Contexto del proyecto para el agente. Se carga en todas las sesiones que se
abran parado en esta carpeta, así que conviene que sea corto y que todo lo que
diga sea cierto.

## Stack

- **FastAPI + Pydantic v2**, Python 3.12+.
- Persistencia en SQLite vía `app/database.py`; el acceso a datos vive en
  `app/repository.py`.
- Sin tests. Es a propósito: es material de las sesiones.

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
| `README-mcp.md` | Cómo levantar los MCP |

El token de GitHub **no va en `.mcp.json`**: se lee de la variable de entorno
`GITHUB_PERSONAL_ACCESS_TOKEN`. Ver `README-mcp.md`.
