from datetime import date

import pytest
from pydantic import ValidationError

from app.list_params import task_list_params_from_query
from app.schemas import TaskCreate, TaskUpdate


def test_task_create_defaults():
    task = TaskCreate(title="X")
    data = task.model_dump(mode="json")
    assert data["prioridad"] == "media"
    assert data["fecha_limite"] is None


def test_task_create_rejects_invalid_prioridad():
    with pytest.raises(ValidationError):
        TaskCreate(title="X", prioridad="invalida")


def test_task_create_rejects_invalid_fecha_limite():
    with pytest.raises(ValidationError):
        TaskCreate(title="X", fecha_limite="15-07-2026")


def test_task_update_forbids_prioridad_and_fecha_limite():
    with pytest.raises(ValidationError):
        TaskUpdate(title="Y", prioridad="alta")

    with pytest.raises(ValidationError):
        TaskUpdate(title="Y", fecha_limite="2026-07-15")


def test_task_list_params_valid_csv():
    params = task_list_params_from_query({"prioridad": "alta,media"})
    assert [p.value for p in params.prioridad or []] == ["alta", "media"]


def test_task_list_params_rejects_invalid_prioridad():
    with pytest.raises(ValidationError):
        task_list_params_from_query({"prioridad": "alta,invalida"})


def test_task_list_params_rejects_invalid_date():
    with pytest.raises(ValidationError):
        task_list_params_from_query({"fecha_desde": "2026/07/01"})


def test_task_list_params_rejects_incoherent_range():
    with pytest.raises(ValidationError):
        task_list_params_from_query(
            {"fecha_desde": "2026-07-31", "fecha_hasta": "2026-07-01"}
        )


def test_post_task_defaults(client):
    response = client.post("/tasks", json={"title": "X"})
    assert response.status_code == 201
    data = response.json()
    assert data["prioridad"] == "media"
    assert data["fecha_limite"] is None


def test_post_task_with_priority_and_due_date(client):
    response = client.post(
        "/tasks",
        json={"title": "Urgente", "prioridad": "alta", "fecha_limite": "2026-07-15"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["prioridad"] == "alta"
    assert data["fecha_limite"] == "2026-07-15"


def test_post_task_invalid_prioridad_returns_422(client):
    response = client.post("/tasks", json={"title": "X", "prioridad": "invalida"})
    assert response.status_code == 422


def test_post_task_invalid_fecha_limite_returns_422(client):
    response = client.post("/tasks", json={"title": "X", "fecha_limite": "15-07-2026"})
    assert response.status_code == 422


def test_put_rejects_prioridad(client):
    created = client.post("/tasks", json={"title": "Original", "prioridad": "baja"}).json()
    response = client.put(
        f"/tasks/{created['id']}",
        json={"title": "Nuevo", "prioridad": "alta"},
    )
    assert response.status_code == 422

    task = client.get(f"/tasks/{created['id']}").json()
    assert task["prioridad"] == "baja"
    assert task["title"] == "Original"


def test_put_rejects_fecha_limite(client):
    created = client.post(
        "/tasks",
        json={"title": "Con fecha", "fecha_limite": "2026-07-10"},
    ).json()
    response = client.put(
        f"/tasks/{created['id']}",
        json={"fecha_limite": "2026-07-20"},
    )
    assert response.status_code == 422

    task = client.get(f"/tasks/{created['id']}").json()
    assert task["fecha_limite"] == "2026-07-10"


def test_put_allows_title_update(client):
    created = client.post(
        "/tasks",
        json={"title": "Viejo", "prioridad": "alta", "fecha_limite": "2026-07-10"},
    ).json()
    response = client.put(f"/tasks/{created['id']}", json={"title": "Nuevo"})
    assert response.status_code == 200

    task = client.get(f"/tasks/{created['id']}").json()
    assert task["title"] == "Nuevo"
    assert task["prioridad"] == "alta"
    assert task["fecha_limite"] == "2026-07-10"


def test_patch_complete_preserves_priority_and_due_date(client):
    created = client.post(
        "/tasks",
        json={"title": "Completar", "prioridad": "alta", "fecha_limite": "2026-07-10"},
    ).json()
    response = client.patch(f"/tasks/{created['id']}/complete")
    assert response.status_code == 200

    task = response.json()
    assert task["completed"] is True
    assert task["prioridad"] == "alta"
    assert task["fecha_limite"] == "2026-07-10"


def _create(client, title: str, prioridad: str = "media", fecha_limite: str | None = None):
    payload: dict[str, object] = {"title": title, "prioridad": prioridad}
    if fecha_limite is not None:
        payload["fecha_limite"] = fecha_limite
    return client.post("/tasks", json=payload).json()


def test_filter_by_single_priority(client):
    _create(client, "Alta 1", "alta")
    _create(client, "Media 1", "media")
    _create(client, "Baja 1", "baja")

    response = client.get("/tasks", params={"prioridad": "alta"})
    assert response.status_code == 200
    titles = [task["title"] for task in response.json()]
    assert titles == ["Alta 1"]


def test_filter_by_multiple_priorities(client):
    _create(client, "Alta", "alta")
    _create(client, "Media", "media")
    _create(client, "Baja", "baja")

    response = client.get("/tasks", params={"prioridad": "alta,media"})
    titles = {task["title"] for task in response.json()}
    assert titles == {"Alta", "Media"}


def test_filter_by_date_range(client):
    _create(client, "Junio", "media", "2026-06-20")
    _create(client, "Julio", "media", "2026-07-10")
    _create(client, "Sin fecha", "media", None)

    response = client.get(
        "/tasks",
        params={"fecha_desde": "2026-07-01", "fecha_hasta": "2026-07-31"},
    )
    titles = [task["title"] for task in response.json()]
    assert titles == ["Julio"]


def test_filter_vencidas(client, freeze_today):
    freeze_today(date(2026, 7, 3))
    _create(client, "Vencida", "alta", "2026-07-02")
    _create(client, "Hoy", "alta", "2026-07-03")
    completed = _create(client, "Completada vencida", "alta", "2026-07-01")
    client.patch(f"/tasks/{completed['id']}/complete")

    response = client.get("/tasks", params={"vencidas": "1"})
    titles = [task["title"] for task in response.json()]
    assert titles == ["Vencida"]


def test_filter_sin_fecha(client):
    _create(client, "Con fecha", "media", "2026-07-10")
    _create(client, "Sin fecha", "media", None)

    response = client.get("/tasks", params={"sin_fecha": "1"})
    titles = [task["title"] for task in response.json()]
    assert titles == ["Sin fecha"]


def test_filter_combined_priority_and_vencidas(client, freeze_today):
    freeze_today(date(2026, 7, 3))
    _create(client, "Alta vencida", "alta", "2026-07-01")
    _create(client, "Media vencida", "media", "2026-07-01")
    _create(client, "Alta ok", "alta", "2026-07-10")

    response = client.get("/tasks", params={"prioridad": "alta", "vencidas": "1"})
    titles = [task["title"] for task in response.json()]
    assert titles == ["Alta vencida"]


def test_default_order(client):
    _create(client, "Baja tarde", "baja", "2026-07-20")
    _create(client, "Alta sin fecha", "alta", None)
    _create(client, "Alta pronto", "alta", "2026-07-05")
    _create(client, "Media", "media", "2026-07-10")

    response = client.get("/tasks")
    titles = [task["title"] for task in response.json()]
    assert titles == ["Alta pronto", "Alta sin fecha", "Media", "Baja tarde"]


def test_order_prioridad_asc(client):
    _create(client, "Alta", "alta")
    _create(client, "Media", "media")
    _create(client, "Baja", "baja")

    response = client.get("/tasks", params={"orden": "prioridad", "dir": "asc"})
    prioridades = [task["prioridad"] for task in response.json()]
    assert prioridades == ["baja", "media", "alta"]


def test_order_fecha_limite_asc_puts_nulls_last(client):
    _create(client, "Sin", "media", None)
    _create(client, "Tarde", "media", "2026-07-20")
    _create(client, "Pronto", "media", "2026-07-05")

    response = client.get("/tasks", params={"orden": "fecha_limite", "dir": "asc"})
    titles = [task["title"] for task in response.json()]
    assert titles == ["Pronto", "Tarde", "Sin"]


def test_order_fecha_limite_desc_puts_nulls_last(client):
    _create(client, "Sin", "media", None)
    _create(client, "Tarde", "media", "2026-07-20")
    _create(client, "Pronto", "media", "2026-07-05")

    response = client.get("/tasks", params={"orden": "fecha_limite", "dir": "desc"})
    titles = [task["title"] for task in response.json()]
    assert titles == ["Tarde", "Pronto", "Sin"]
