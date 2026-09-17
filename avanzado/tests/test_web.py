import re

from fastapi.testclient import TestClient


def _items(html: str) -> dict[str, str]:
    """Devuelve el HTML de cada <li> de la lista, indexado por el título de la tarea."""
    items = {}
    for block in re.findall(r"<li .*?</li>", html, flags=re.DOTALL):
        title = re.search(r'<div class="title">(.*?)</div>', block).group(1)
        items[title] = block
    return items


def test_pagina_muestra_prioridad_y_fecha_limite(client: TestClient, sample_tasks: dict) -> None:
    items = _items(client.get("/").text)

    assert "Prioridad: alta" in items["futura"]
    assert f"Vence: {sample_tasks['futura']['due_date']}" in items["futura"]
    assert "Prioridad: baja" in items["sin_fecha"]
    assert "Vence:" not in items["sin_fecha"]


def test_pagina_marca_las_mismas_vencidas_que_la_api(client: TestClient, sample_tasks: dict) -> None:
    items = _items(client.get("/").text)

    marcadas = [title for title, block in items.items() if block.startswith('<li class="overdue"')]
    vencidas_api = [t["title"] for t in client.get("/tasks?overdue=true").json()]
    assert marcadas == vencidas_api == ["vencida"]
    assert "Vencida" not in items["completada_vencida"]


def test_api_no_expone_is_overdue(client: TestClient, sample_tasks: dict) -> None:
    assert all("is_overdue" not in t for t in client.get("/tasks").json())


def test_completar_y_borrar_desde_la_pagina_siguen_funcionando(client: TestClient, sample_tasks: dict) -> None:
    task_id = sample_tasks["futura"]["id"]

    completar = client.post(f"/ui/tasks/{task_id}/complete", follow_redirects=False)
    assert completar.status_code == 303
    assert client.get(f"/tasks/{task_id}").json()["completed"] is True

    borrar = client.post(f"/ui/tasks/{task_id}/delete", follow_redirects=False)
    assert borrar.status_code == 303
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_formulario_de_alta_preselecciona_media(client: TestClient) -> None:
    assert '<option value="media" selected>' in client.get("/").text


def test_alta_desde_la_pagina_con_prioridad_y_fecha(client: TestClient) -> None:
    response = client.post(
        "/ui/tasks",
        data={"title": "Con fecha", "description": "", "priority": "alta", "due_date": "2026-12-31"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    item = _items(client.get("/").text)["Con fecha"]
    assert "Prioridad: alta" in item
    assert "Vence: 2026-12-31" in item


def test_alta_desde_la_pagina_sin_fecha_la_guarda_nula(client: TestClient) -> None:
    client.post("/ui/tasks", data={"title": "Sin fecha", "priority": "baja", "due_date": ""})

    [task] = client.get("/tasks").json()
    assert task["due_date"] is None
    assert task["priority"] == "baja"


def test_alta_desde_la_pagina_sin_prioridad_queda_en_media(client: TestClient) -> None:
    client.post("/ui/tasks", data={"title": "Sin prioridad"})

    [task] = client.get("/tasks").json()
    assert task["priority"] == "media"
