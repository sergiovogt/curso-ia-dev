import sqlite3
from pathlib import Path

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
