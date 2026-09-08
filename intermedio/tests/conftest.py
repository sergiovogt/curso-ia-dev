from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setattr("app.database.DB_PATH", tmp_path / "test.db")
    with TestClient(app) as test_client:
        yield test_client
