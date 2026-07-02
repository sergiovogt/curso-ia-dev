---
name: code-review-fastapi
description: Code review de endpoints FastAPI del módulo intermedio según las convenciones del equipo.
---

# Code Review FastAPI — Intermedio

Cuando el usuario pida review de la API:

1. Leer el archivo indicado (por defecto `intermedio/app/main.py`).
2. Evaluar cada punto contra las convenciones en `intermedio/docs/CODING_STANDARDS.md`.
3. Reportar en este formato exacto:

---

## Qué cumple
- [listar lo que ya sigue las convenciones]

## Incumplimientos

| Severidad | Regla incumplida | Ubicación | Mejora sugerida |
|-----------|-----------------|-----------|-----------------|
| Alta      | ...             | L##       | ...             |
| Media     | ...             | L##       | ...             |
| Baja      | ...             | L##       | ...             |

---

4. No modificar el código salvo que el usuario lo pida explícitamente.
5. Si el usuario no indica un archivo, asumir `intermedio/app/main.py`.
