import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.database import init_db

# Esquema anterior a prioridad y fecha límite, copiado literal: el código ya tiene el nuevo.
_OLD_SCHEMA = """
    CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        completed BOOLEAN NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
"""


def _rows(db_path: Path) -> list[sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    finally:
        conn.close()


@pytest.fixture
def old_db(tmp_path, monkeypatch) -> Path:
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(db_path)
    conn.execute(_OLD_SCHEMA)
    conn.executemany(
        "INSERT INTO tasks (title, description, completed, created_at) VALUES (?, ?, ?, ?)",
        [
            ("Vieja 1", None, 0, "2026-01-01T10:00:00+00:00"),
            ("Vieja 2", "Con detalle", 1, "2026-01-02T10:00:00+00:00"),
        ],
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr("app.database.DB_PATH", db_path)
    return db_path


def test_init_db_migra_una_base_vieja_sin_perder_tareas(old_db: Path) -> None:
    init_db()

    rows = _rows(old_db)
    assert [(r["title"], r["description"], r["completed"]) for r in rows] == [
        ("Vieja 1", None, 0),
        ("Vieja 2", "Con detalle", 1),
    ]
    assert all(r["priority"] == "media" for r in rows)
    assert all(r["due_date"] is None for r in rows)


def test_init_db_dos_veces_no_falla_ni_duplica(old_db: Path) -> None:
    init_db()
    init_db()

    assert len(_rows(old_db)) == 2


def test_seed_trae_prioridades_y_fechas(seeded_client: TestClient, tmp_path) -> None:
    rows = _rows(tmp_path / "test.db")

    assert [(r["title"], r["completed"], r["priority"], r["due_date"]) for r in rows] == [
        ("Configurar el pipeline de CI", 1, "alta", "2026-06-10"),
        ("Migrar el login a OAuth", 0, "alta", "2026-07-01"),
        ("Escribir la doc del endpoint de pagos", 0, "baja", None),
        ("Revisar el PR de checkout", 0, "media", "2027-12-15"),
        ("Actualizar dependencias de FastAPI", 1, "media", None),
    ]
