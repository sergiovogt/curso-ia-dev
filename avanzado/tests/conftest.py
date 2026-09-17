import sqlite3
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
