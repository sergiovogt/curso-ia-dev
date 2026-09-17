import sqlite3
from datetime import date, timedelta
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def seeded_client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setattr("app.database.DB_PATH", tmp_path / "test.db")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client(seeded_client: TestClient, tmp_path) -> TestClient:
    conn = sqlite3.connect(tmp_path / "test.db")
    try:
        conn.execute("DELETE FROM tasks")
        conn.commit()
    finally:
        conn.close()
    return seeded_client


@pytest.fixture
def sample_tasks(client: TestClient) -> dict[str, dict]:
    """Juego de tareas que cubre todos los casos de "vencida", con fechas relativas a hoy."""
    today = date.today()
    payloads = {
        "vencida": {"priority": "alta", "due_date": today - timedelta(days=1)},
        "vence_hoy": {"priority": "media", "due_date": today},
        "futura": {"priority": "alta", "due_date": today + timedelta(days=1)},
        "sin_fecha": {"priority": "baja", "due_date": None},
        "completada_vencida": {"priority": "alta", "due_date": today - timedelta(days=1), "completed": True},
    }
    tasks = {}
    for name, payload in payloads.items():
        body = {**payload, "title": name}
        if body["due_date"] is not None:
            body["due_date"] = body["due_date"].isoformat()
        tasks[name] = client.post("/tasks", json=body).json()
    return tasks
