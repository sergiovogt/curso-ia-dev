from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


def test_list_tasks_sin_parametros_ordena_por_id(client: TestClient) -> None:
    ids = [client.post("/tasks", json={"title": f"Tarea {n}"}).json()["id"] for n in range(3)]

    response = client.get("/tasks")

    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == ids


def test_create_task_sin_prioridad_queda_en_media(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "x"})

    assert response.status_code == 201
    assert response.json()["priority"] == "media"


def test_create_task_con_prioridad_la_persiste(client: TestClient) -> None:
    creada = client.post("/tasks", json={"title": "x", "priority": "alta"}).json()

    assert creada["priority"] == "alta"
    assert client.get(f"/tasks/{creada['id']}").json()["priority"] == "alta"


@pytest.mark.parametrize("priority", ["urgente", None])
def test_create_task_con_prioridad_invalida_devuelve_422(client: TestClient, priority: str | None) -> None:
    response = client.post("/tasks", json={"title": "x", "priority": priority})

    assert response.status_code == 422


def test_update_task_cambia_solo_la_prioridad(client: TestClient) -> None:
    creada = client.post(
        "/tasks", json={"title": "x", "description": "d", "completed": True, "priority": "alta"}
    ).json()

    response = client.put(f"/tasks/{creada['id']}", json={"priority": "baja"})

    assert response.status_code == 200
    assert response.json() == {**creada, "priority": "baja"}


def test_update_task_con_prioridad_nula_devuelve_422(client: TestClient) -> None:
    creada = client.post("/tasks", json={"title": "x", "priority": "alta"}).json()

    response = client.put(f"/tasks/{creada['id']}", json={"priority": None})

    assert response.status_code == 422
    assert client.get(f"/tasks/{creada['id']}").json()["priority"] == "alta"


def test_complete_task_incluye_la_prioridad(client: TestClient) -> None:
    creada = client.post("/tasks", json={"title": "x", "priority": "baja"}).json()

    response = client.patch(f"/tasks/{creada['id']}/complete")

    assert response.json()["priority"] == "baja"


def test_create_task_sin_fecha_limite_queda_nula(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "x"})

    assert response.json()["due_date"] is None


def test_create_task_con_fecha_limite_la_persiste(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "x", "priority": "alta", "due_date": "2026-12-31"})

    assert response.status_code == 201
    creada = response.json()
    assert creada["due_date"] == "2026-12-31"
    assert client.get(f"/tasks/{creada['id']}").json() == creada


def test_create_task_acepta_fecha_limite_pasada(client: TestClient) -> None:
    ayer = (date.today() - timedelta(days=1)).isoformat()

    response = client.post("/tasks", json={"title": "x", "due_date": ayer})

    assert response.status_code == 201
    assert response.json()["due_date"] == ayer


@pytest.mark.parametrize("due_date", ["31/12/2026", "2026-12-31T10:00:00"])
def test_create_task_con_fecha_limite_invalida_devuelve_422(client: TestClient, due_date: str) -> None:
    response = client.post("/tasks", json={"title": "x", "due_date": due_date})

    assert response.status_code == 422


def test_update_task_con_fecha_nula_la_borra(client: TestClient) -> None:
    creada = client.post("/tasks", json={"title": "x", "due_date": "2026-12-31"}).json()

    response = client.put(f"/tasks/{creada['id']}", json={"due_date": None})

    assert response.json()["due_date"] is None
    assert client.get(f"/tasks/{creada['id']}").json()["due_date"] is None


def test_update_task_cambia_solo_la_fecha_limite(client: TestClient) -> None:
    creada = client.post(
        "/tasks", json={"title": "x", "description": "d", "completed": True, "priority": "alta"}
    ).json()

    response = client.put(f"/tasks/{creada['id']}", json={"due_date": "2027-01-15"})

    assert response.json() == {**creada, "due_date": "2027-01-15"}


def test_complete_task_incluye_la_fecha_limite(client: TestClient) -> None:
    creada = client.post("/tasks", json={"title": "x", "due_date": "2026-12-31"}).json()

    response = client.patch(f"/tasks/{creada['id']}/complete")

    assert response.json()["due_date"] == "2026-12-31"
