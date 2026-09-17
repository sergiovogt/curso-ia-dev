from fastapi.testclient import TestClient


def test_list_tasks_sin_parametros_ordena_por_id(client: TestClient) -> None:
    ids = [client.post("/tasks", json={"title": f"Tarea {n}"}).json()["id"] for n in range(3)]

    response = client.get("/tasks")

    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == ids
