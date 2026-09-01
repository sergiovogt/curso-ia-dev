import sqlite3
from pathlib import Path

import pytest

from app.database import _migrate_add_priority_and_due_date, get_connection, init_db
from app.schemas import Prioridad


def _create_legacy_db(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    seed_tasks = [
        ("Tarea 1", "Desc 1", 1, "2026-06-02T09:15:00+00:00"),
        ("Tarea 2", None, 0, "2026-06-05T14:30:00+00:00"),
        ("Tarea 3", None, 0, "2026-06-09T11:00:00+00:00"),
        ("Tarea 4", "Desc 4", 0, "2026-06-12T16:45:00+00:00"),
        ("Tarea 5", None, 1, "2026-06-16T08:20:00+00:00"),
    ]
    conn.executemany(
        "INSERT INTO tasks (title, description, completed, created_at) VALUES (?, ?, ?, ?)",
        seed_tasks,
    )
    conn.commit()
    conn.close()


def test_migration_adds_columns_and_defaults_on_legacy_seed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    _create_legacy_db(db_path)
    monkeypatch.setattr("app.database.DB_PATH", db_path)

    init_db()

    conn = get_connection()
    try:
        columns = {row[1]: row for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
        assert "prioridad" in columns
        assert "fecha_limite" in columns
        assert "media" in (columns["prioridad"][4] or "")

        rows = conn.execute("SELECT prioridad, fecha_limite FROM tasks ORDER BY id").fetchall()
        assert len(rows) == 5
        for row in rows:
            assert row["prioridad"] == Prioridad.media.value
            assert row["fecha_limite"] is None
    finally:
        conn.close()


def test_migration_is_idempotent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    _create_legacy_db(db_path)
    monkeypatch.setattr("app.database.DB_PATH", db_path)

    init_db()
    init_db()

    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        assert count == 5
    finally:
        conn.close()


def test_migrate_function_checks_columns_individually(tmp_path: Path):
    db_path = tmp_path / "partial.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media'
        )
        """
    )
    conn.commit()

    _migrate_add_priority_and_due_date(conn)

    columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
    assert "prioridad" in columns
    assert "fecha_limite" in columns
    conn.close()
