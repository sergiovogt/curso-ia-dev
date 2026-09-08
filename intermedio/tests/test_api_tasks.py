from fastapi.testclient import TestClient


def test_create_task_devuelve_201_y_asigna_id(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Comprar pan"})

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["title"] == "Comprar pan"


def test_create_task_aplica_los_defaults(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Tarea sin opcionales"})

    body = response.json()
    assert body["completed"] is False
    assert body["priority"] == 0
    assert body["description"] is None


def test_create_task_conserva_los_campos_opcionales(client: TestClient) -> None:
    response = client.post(
        "/tasks",
        json={"title": "Tarea completa", "description": "Con detalle", "completed": True},
    )

    body = response.json()
    assert body["description"] == "Con detalle"
    assert body["completed"] is True


def test_create_task_persiste_la_tarea(client: TestClient) -> None:
    creada = client.post("/tasks", json={"title": "Persistida"}).json()

    guardada = client.get(f"/tasks/{creada['id']}")

    assert guardada.status_code == 200
    assert guardada.json() == creada


def test_create_task_rechaza_title_vacio(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": ""})

    assert response.status_code == 422


def test_create_task_rechaza_title_ausente(client: TestClient) -> None:
    response = client.post("/tasks", json={"description": "Sin titulo"})

    assert response.status_code == 422
