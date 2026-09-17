from fastapi.testclient import TestClient


# --- Humo ---


def test_list_tasks_devuelve_las_tareas_sembradas(client: TestClient) -> None:
    response = client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 5
