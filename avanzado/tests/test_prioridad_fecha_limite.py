import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

_OLD_SCHEMA = """
    CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        completed BOOLEAN NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
"""

_OLD_ROWS = [
    (1, "Tarea vieja", "Con descripción", 1, "2026-01-02T10:00:00+00:00"),
    (7, "Otra tarea vieja", None, 0, "2026-01-03T11:30:00+00:00"),
]


def _read_rows(db_path: Path) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT id, title, description, completed, created_at, priority, due_date "
            "FROM tasks ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def _start_app() -> None:
    with TestClient(app):
        pass


# --- Humo ---


def test_list_tasks_devuelve_las_tareas_sembradas(client: TestClient) -> None:
    response = client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 5


# --- Migración de la base ---


def test_base_nueva_siembra_con_media_y_sin_fecha(client: TestClient, db_path: Path) -> None:
    rows = _read_rows(db_path)

    assert len(rows) == 5
    assert all(row[5] == "media" and row[6] is None for row in rows)


def test_base_vieja_se_migra_sin_perder_tareas(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(_OLD_SCHEMA)
    conn.executemany(
        "INSERT INTO tasks (id, title, description, completed, created_at) VALUES (?, ?, ?, ?, ?)",
        _OLD_ROWS,
    )
    conn.commit()
    conn.close()

    _start_app()

    assert _read_rows(db_path) == [(*row, "media", None) for row in _OLD_ROWS]


def test_arrancar_dos_veces_no_cambia_los_datos(db_path: Path) -> None:
    _start_app()
    primera = _read_rows(db_path)

    _start_app()

    assert _read_rows(db_path) == primera


# --- API: alta y lectura ---


def test_create_sin_prioridad_ni_fecha_usa_los_defaults(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Sin extras"})

    assert response.status_code == 201
    body = response.json()
    assert body["priority"] == "media"
    assert body["due_date"] is None


def test_create_con_prioridad_y_fecha_las_devuelve(client: TestClient) -> None:
    response = client.post(
        "/tasks", json={"title": "Urgente", "priority": "alta", "due_date": "2026-10-01"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["priority"] == "alta"
    assert body["due_date"] == "2026-10-01"


@pytest.mark.parametrize("priority", ["urgente", None])
def test_create_con_prioridad_invalida_devuelve_422(client: TestClient, priority: str | None) -> None:
    response = client.post("/tasks", json={"title": "Mal", "priority": priority})

    assert response.status_code == 422
    assert len(client.get("/tasks").json()) == 5


@pytest.mark.parametrize(
    "due_date", ["01/10/2026", "2026-10-01T10:00:00", "2026-10-01T00:00:00", 0]
)
def test_create_con_fecha_invalida_devuelve_422(client: TestClient, due_date: str | int) -> None:
    response = client.post("/tasks", json={"title": "Mal", "due_date": due_date})

    assert response.status_code == 422
    assert len(client.get("/tasks").json()) == 5


def test_create_con_fecha_pasada_se_acepta(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Atrasada", "due_date": "2000-01-01"})

    assert response.status_code == 201
    assert response.json()["due_date"] == "2000-01-01"


def test_get_incluye_prioridad_y_fecha(client: TestClient) -> None:
    creada = client.post(
        "/tasks", json={"title": "Con fecha", "priority": "baja", "due_date": "2026-12-24"}
    ).json()

    una = client.get(f"/tasks/{creada['id']}").json()
    todas = client.get("/tasks").json()

    assert (una["priority"], una["due_date"]) == ("baja", "2026-12-24")
    assert all("priority" in t and "due_date" in t for t in todas)


def test_las_tareas_sembradas_salen_en_media_y_sin_fecha(client: TestClient) -> None:
    tareas = client.get("/tasks").json()

    assert all(t["priority"] == "media" and t["due_date"] is None for t in tareas)


# --- API: edición ---


def _crear(client: TestClient, **campos: object) -> dict:
    return client.post("/tasks", json={"title": "Tarea", **campos}).json()


def test_put_solo_prioridad_no_cambia_lo_demas(client: TestClient) -> None:
    creada = _crear(client, description="Detalle", priority="alta", due_date="2026-10-01")

    response = client.put(f"/tasks/{creada['id']}", json={"priority": "baja"})

    assert response.status_code == 200
    assert client.get(f"/tasks/{creada['id']}").json() == {**creada, "priority": "baja"}


def test_put_con_fecha_null_saca_la_fecha(client: TestClient) -> None:
    creada = _crear(client, due_date="2026-10-01")

    client.put(f"/tasks/{creada['id']}", json={"due_date": None})

    assert client.get(f"/tasks/{creada['id']}").json()["due_date"] is None


@pytest.mark.parametrize("priority", [None, "urgente"])
def test_put_con_prioridad_invalida_devuelve_422_sin_cambios(
    client: TestClient, priority: str | None
) -> None:
    creada = _crear(client, priority="alta")

    response = client.put(f"/tasks/{creada['id']}", json={"priority": priority})

    assert response.status_code == 422
    assert client.get(f"/tasks/{creada['id']}").json() == creada


def test_completar_no_cambia_prioridad_ni_fecha(client: TestClient) -> None:
    creada = _crear(client, priority="baja", due_date="2026-10-01")

    client.patch(f"/tasks/{creada['id']}/complete")

    guardada = client.get(f"/tasks/{creada['id']}").json()
    assert (guardada["priority"], guardada["due_date"], guardada["completed"]) == (
        "baja",
        "2026-10-01",
        True,
    )


# --- API: filtros ---


def _ids(response) -> list[int]:
    assert response.status_code == 200
    return [t["id"] for t in response.json()]


def _crear_mezcla(client: TestClient) -> dict[str, int]:
    """Suma a las 5 sembradas (media; 1 y 5 completadas) tareas alta y baja."""
    ids = {
        "alta_pendiente": _crear(client, priority="alta")["id"],
        "alta_completada": _crear(client, priority="alta", completed=True)["id"],
        "baja_pendiente": _crear(client, priority="baja")["id"],
    }
    return ids


def test_filtro_por_prioridad_incluye_completadas(client: TestClient) -> None:
    ids = _crear_mezcla(client)

    assert _ids(client.get("/tasks?priority=alta")) == [ids["alta_pendiente"], ids["alta_completada"]]


def test_filtro_por_completada(client: TestClient) -> None:
    ids = _crear_mezcla(client)

    assert _ids(client.get("/tasks?completed=true")) == [1, 5, ids["alta_completada"]]
    assert _ids(client.get("/tasks?completed=false")) == [
        2, 3, 4, ids["alta_pendiente"], ids["baja_pendiente"]
    ]


def test_filtros_combinados(client: TestClient) -> None:
    ids = _crear_mezcla(client)

    assert _ids(client.get("/tasks?priority=alta&completed=false")) == [ids["alta_pendiente"]]


def test_filtro_con_prioridad_invalida_devuelve_422(client: TestClient) -> None:
    assert client.get("/tasks?priority=urgente").status_code == 422


def test_filtro_sin_coincidencias_devuelve_lista_vacia(client: TestClient) -> None:
    assert _ids(client.get("/tasks?priority=baja")) == []


def test_filtro_vacio_es_sin_filtro(client: TestClient) -> None:
    assert _ids(client.get("/tasks?priority=&completed=")) == [1, 2, 3, 4, 5]
