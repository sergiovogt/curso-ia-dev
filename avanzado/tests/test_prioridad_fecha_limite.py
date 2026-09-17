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
