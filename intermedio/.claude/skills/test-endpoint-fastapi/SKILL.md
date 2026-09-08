---
name: test-endpoint-fastapi
description: Genera tests con pytest y TestClient para los endpoints FastAPI del módulo intermedio.
---

# Test Endpoint FastAPI — Intermedio

Cuando el usuario pida tests de la API:

1. Leer el endpoint indicado. Si no indica ninguno, generar tests para todos los de
   `intermedio/app/main.py`.
2. Escribir los tests en `intermedio/tests/test_api_tasks.py`, con
   `intermedio/tests/conftest.py` como soporte.
3. Cubrir los casos obligatorios de la tabla de más abajo.
4. Cerrar la respuesta con el comando para correrlos. **No ejecutarlos.**

## Qué testear

Testear el comportamiento observable del endpoint **tal como está implementado**; no inventar
casos para funcionalidad ausente. Si el estándar pide algo que el código no tiene (paginación,
`GET /health`, `422` en ids negativos), eso es materia de la skill `code-review-fastapi`, no de
esta.

Casos mínimos por método:

| Endpoint | Casos obligatorios |
|---|---|
| `POST /tasks` | `201`; body con `id` asignado; defaults correctos (`completed: false`, `priority: 0`); `422` con `title` vacío |
| `GET /tasks` | `200`; devuelve lista; refleja las tareas creadas en el test |
| `GET /tasks/{id}` | `200` en el happy path; `404` con id inexistente |
| `PUT /tasks/{id}` | actualización parcial: mandar solo `title` **no** debe pisar `description` ni `completed`; `404` con id inexistente |
| `PATCH /tasks/{id}/complete` | `completed: true` en la respuesta; `404` con id inexistente |
| `DELETE /tasks/{id}` | `204` sin body; un segundo `DELETE` del mismo id devuelve `404` |

En **todos** los casos `404`, assertear el mensaje textual:

```python
assert response.json()["detail"] == f"Tarea con id {task_id} no encontrada"
```

## Aislamiento de la base

`app.database.DB_PATH` apunta al `tasks.db` real del nivel. Sin aislamiento, los tests escriben
sobre esa base y borran los datos de trabajo. El `conftest.py` es obligatorio y va así:

```python
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setattr("app.database.DB_PATH", tmp_path / "test.db")
    with TestClient(app) as test_client:
        yield test_client
```

Dos detalles que no se pueden cambiar:

- El `monkeypatch` va **antes** de instanciar el `TestClient`.
- El `with` es obligatorio. `TestClient(app)` sin context manager no dispara el `lifespan`, así
  que no corre `init_db()` y los tests fallan con `no such table: tasks`.

Cada test recibe la fixture `client` y una base vacía.

## Alcance

- Escribir únicamente bajo `intermedio/tests/`. **No modificar `app/`**, ni aunque durante la
  generación parezca que hay un bug: reportarlo en la respuesta y seguir.
- Si `tests/test_api_tasks.py` ya existe, agregar las funciones nuevas al final. No reescribir el
  archivo, no duplicar imports ni fixtures.

## Cierre

Terminar indicando el comando, parado en `intermedio/`:

```bash
python -m pytest tests/test_api_tasks.py -q
```

El `python -m` es necesario: pone el cwd en `sys.path` para que resuelvan los `from app...`. No
hay `pytest.ini` ni `pyproject.toml` en el nivel que lo haga por vos.
