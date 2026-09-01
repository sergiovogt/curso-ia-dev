from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "test_tasks.db"
    monkeypatch.setattr("app.database.DB_PATH", db_path)

    from app.database import get_connection
    from app.main import app

    with TestClient(app) as test_client:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM tasks")
            conn.commit()
        finally:
            conn.close()
        yield test_client


@pytest.fixture
def freeze_today(monkeypatch: pytest.MonkeyPatch):
    def _freeze(fixed: date) -> None:
        monkeypatch.setattr("app.dates.today_app", lambda: fixed)
        monkeypatch.setattr("app.main.today_app", lambda: fixed)

    return _freeze
