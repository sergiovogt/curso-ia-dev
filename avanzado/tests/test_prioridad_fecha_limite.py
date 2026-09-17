import re
import sqlite3
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

_OLD_SCHEMA = """
    CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        completed BOOLEAN NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
"""

_OLD_ROWS = [
    (1, "Tarea vieja", "Con descripción", 1, "2026-01-02T10:00:00+00:00"),
    (7, "Otra tarea vieja", None, 0, "2026-01-03T11:30:00+00:00"),
]


def _read_rows(db_path: Path) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            "SELECT id, title, description, completed, created_at, priority, due_date "
            "FROM tasks ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def _start_app() -> None:
    with TestClient(app):
        pass


# --- Humo ---


def test_list_tasks_devuelve_las_tareas_sembradas(client: TestClient) -> None:
    response = client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 5


# --- Migración de la base ---


def test_base_nueva_siembra_con_media_y_sin_fecha(client: TestClient, db_path: Path) -> None:
    rows = _read_rows(db_path)

    assert len(rows) == 5
    assert all(row[5] == "media" and row[6] is None for row in rows)


def test_base_vieja_se_migra_sin_perder_tareas(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(_OLD_SCHEMA)
    conn.executemany(
        "INSERT INTO tasks (id, title, description, completed, created_at) VALUES (?, ?, ?, ?, ?)",
        _OLD_ROWS,
    )
    conn.commit()
    conn.close()

    _start_app()

    assert _read_rows(db_path) == [(*row, "media", None) for row in _OLD_ROWS]


def test_arrancar_dos_veces_no_cambia_los_datos(db_path: Path) -> None:
    _start_app()
    primera = _read_rows(db_path)

    _start_app()

    assert _read_rows(db_path) == primera


# --- API: alta y lectura ---


def test_create_sin_prioridad_ni_fecha_usa_los_defaults(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Sin extras"})

    assert response.status_code == 201
    body = response.json()
    assert body["priority"] == "media"
    assert body["due_date"] is None


def test_create_con_prioridad_y_fecha_las_devuelve(client: TestClient) -> None:
    response = client.post(
        "/tasks", json={"title": "Urgente", "priority": "alta", "due_date": "2026-10-01"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["priority"] == "alta"
    assert body["due_date"] == "2026-10-01"


@pytest.mark.parametrize("priority", ["urgente", None])
def test_create_con_prioridad_invalida_devuelve_422(client: TestClient, priority: str | None) -> None:
    response = client.post("/tasks", json={"title": "Mal", "priority": priority})

    assert response.status_code == 422
    assert len(client.get("/tasks").json()) == 5


@pytest.mark.parametrize(
    "due_date", ["01/10/2026", "2026-10-01T10:00:00", "2026-10-01T00:00:00", 0]
)
def test_create_con_fecha_invalida_devuelve_422(client: TestClient, due_date: str | int) -> None:
    response = client.post("/tasks", json={"title": "Mal", "due_date": due_date})

    assert response.status_code == 422
    assert len(client.get("/tasks").json()) == 5


def test_create_con_fecha_pasada_se_acepta(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Atrasada", "due_date": "2000-01-01"})

    assert response.status_code == 201
    assert response.json()["due_date"] == "2000-01-01"


def test_get_incluye_prioridad_y_fecha(client: TestClient) -> None:
    creada = client.post(
        "/tasks", json={"title": "Con fecha", "priority": "baja", "due_date": "2026-12-24"}
    ).json()

    una = client.get(f"/tasks/{creada['id']}").json()
    todas = client.get("/tasks").json()

    assert (una["priority"], una["due_date"]) == ("baja", "2026-12-24")
    assert all("priority" in t and "due_date" in t for t in todas)


def test_las_tareas_sembradas_salen_en_media_y_sin_fecha(client: TestClient) -> None:
    tareas = client.get("/tasks").json()

    assert all(t["priority"] == "media" and t["due_date"] is None for t in tareas)


# --- API: edición ---


def _crear(client: TestClient, **campos: object) -> dict:
    return client.post("/tasks", json={"title": "Tarea", **campos}).json()


def test_put_solo_prioridad_no_cambia_lo_demas(client: TestClient) -> None:
    creada = _crear(client, description="Detalle", priority="alta", due_date="2026-10-01")

    response = client.put(f"/tasks/{creada['id']}", json={"priority": "baja"})

    assert response.status_code == 200
    assert client.get(f"/tasks/{creada['id']}").json() == {**creada, "priority": "baja"}


def test_put_con_fecha_null_saca_la_fecha(client: TestClient) -> None:
    creada = _crear(client, due_date="2026-10-01")

    client.put(f"/tasks/{creada['id']}", json={"due_date": None})

    assert client.get(f"/tasks/{creada['id']}").json()["due_date"] is None


@pytest.mark.parametrize("priority", [None, "urgente"])
def test_put_con_prioridad_invalida_devuelve_422_sin_cambios(
    client: TestClient, priority: str | None
) -> None:
    creada = _crear(client, priority="alta")

    response = client.put(f"/tasks/{creada['id']}", json={"priority": priority})

    assert response.status_code == 422
    assert client.get(f"/tasks/{creada['id']}").json() == creada


def test_completar_no_cambia_prioridad_ni_fecha(client: TestClient) -> None:
    creada = _crear(client, priority="baja", due_date="2026-10-01")

    client.patch(f"/tasks/{creada['id']}/complete")

    guardada = client.get(f"/tasks/{creada['id']}").json()
    assert (guardada["priority"], guardada["due_date"], guardada["completed"]) == (
        "baja",
        "2026-10-01",
        True,
    )


# --- API: filtros ---


def _ids(response) -> list[int]:
    assert response.status_code == 200
    return [t["id"] for t in response.json()]


def _crear_mezcla(client: TestClient) -> dict[str, int]:
    """Suma a las 5 sembradas (media; 1 y 5 completadas) tareas alta y baja."""
    return {
        "alta_pendiente": _crear(client, priority="alta")["id"],
        "alta_completada": _crear(client, priority="alta", completed=True)["id"],
        "baja_pendiente": _crear(client, priority="baja")["id"],
    }


def test_filtro_por_prioridad_incluye_completadas(client: TestClient) -> None:
    ids = _crear_mezcla(client)

    assert _ids(client.get("/tasks?priority=alta")) == [ids["alta_pendiente"], ids["alta_completada"]]


def test_filtro_por_completada(client: TestClient) -> None:
    ids = _crear_mezcla(client)

    assert _ids(client.get("/tasks?completed=true")) == [1, 5, ids["alta_completada"]]
    assert _ids(client.get("/tasks?completed=false")) == [
        2, 3, 4, ids["alta_pendiente"], ids["baja_pendiente"]
    ]


def test_filtros_combinados(client: TestClient) -> None:
    ids = _crear_mezcla(client)

    assert _ids(client.get("/tasks?priority=alta&completed=false")) == [ids["alta_pendiente"]]


def test_filtro_con_prioridad_invalida_devuelve_422(client: TestClient) -> None:
    assert client.get("/tasks?priority=urgente").status_code == 422


def test_filtro_sin_coincidencias_devuelve_lista_vacia(client: TestClient) -> None:
    assert _ids(client.get("/tasks?priority=baja")) == []


def test_filtro_vacio_es_sin_filtro(client: TestClient) -> None:
    assert _ids(client.get("/tasks?priority=&completed=")) == [1, 2, 3, 4, 5]


# --- API: orden ---


def test_sin_sort_ordena_por_id(client: TestClient) -> None:
    _crear_mezcla(client)

    ids = _ids(client.get("/tasks"))

    assert ids == sorted(ids)


def test_sort_priority_ordena_alta_media_baja_y_desempata_por_id(client: TestClient) -> None:
    for sembrada in range(1, 6):
        client.delete(f"/tasks/{sembrada}")
    baja = _crear(client, priority="baja")["id"]
    alta_1 = _crear(client, priority="alta")["id"]
    media = _crear(client, priority="media")["id"]
    alta_2 = _crear(client, priority="alta")["id"]

    assert _ids(client.get("/tasks?sort=priority")) == [alta_1, alta_2, media, baja]


def test_sort_combinado_con_filtros(client: TestClient) -> None:
    ids = _crear_mezcla(client)
    media_pendiente = _crear(client, priority="media")["id"]

    assert _ids(client.get("/tasks?sort=priority&priority=media&completed=false")) == [
        2, 3, 4, media_pendiente
    ]
    assert _ids(client.get("/tasks?sort=priority&completed=false")) == [
        ids["alta_pendiente"], 2, 3, 4, media_pendiente, ids["baja_pendiente"]
    ]


def test_sort_invalido_devuelve_422(client: TestClient) -> None:
    assert client.get("/tasks?sort=due_date").status_code == 422


# --- Página: prioridad, fecha y vencidas ---


def _li(html: str, task_id: int) -> str:
    match = re.search(rf'<li[^>]*data-id="{task_id}".*?</li>', html, re.DOTALL)
    assert match is not None, f"no está la tarea {task_id} en la página"
    return match.group(0)


def test_pagina_muestra_prioridad_y_fecha(client: TestClient) -> None:
    con_fecha = _crear(client, priority="alta", due_date="2999-12-31")["id"]
    sin_fecha = _crear(client, priority="baja")["id"]

    html = client.get("/").text

    assert "alta" in _li(html, con_fecha) and "2999-12-31" in _li(html, con_fecha)
    assert "baja" in _li(html, sin_fecha) and "Vence" not in _li(html, sin_fecha)


def test_pagina_marca_solo_las_pendientes_con_fecha_pasada(client: TestClient) -> None:
    vencida = _crear(client, due_date="2000-01-01")["id"]
    no_vencidas = [
        _crear(client, due_date="2000-01-01", completed=True)["id"],
        _crear(client, due_date=date.today().isoformat())["id"],
        _crear(client, due_date="2999-12-31")["id"],
        _crear(client)["id"],
    ]

    html = client.get("/").text

    assert "Vencida" in _li(html, vencida)
    assert "overdue" in _li(html, vencida)
    for task_id in no_vencidas:
        assert "Vencida" not in _li(html, task_id)
        assert "overdue" not in _li(html, task_id)


# --- Página: alta con prioridad y fecha ---


def _ultima(client: TestClient) -> dict:
    return client.get("/tasks").json()[-1]


def test_alta_desde_la_pagina_con_prioridad_y_fecha(client: TestClient) -> None:
    response = client.post(
        "/ui/tasks",
        data={"title": "Desde la web", "priority": "alta", "due_date": "2026-10-01"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    creada = client.get(f"/tasks/{_ultima(client)['id']}").json()
    assert (creada["title"], creada["priority"], creada["due_date"]) == (
        "Desde la web",
        "alta",
        "2026-10-01",
    )


def test_alta_desde_la_pagina_con_fecha_vacia(client: TestClient) -> None:
    client.post("/ui/tasks", data={"title": "Sin fecha", "priority": "baja", "due_date": ""})

    assert _ultima(client)["due_date"] is None


def test_alta_desde_la_pagina_sin_prioridad_queda_en_media(client: TestClient) -> None:
    client.post("/ui/tasks", data={"title": "Sin prioridad"})

    assert _ultima(client)["priority"] == "media"


def test_alta_desde_la_pagina_con_fecha_invalida_devuelve_422(client: TestClient) -> None:
    response = client.post("/ui/tasks", data={"title": "Mal", "due_date": "01/10/2026"})

    assert response.status_code == 422
    assert len(client.get("/tasks").json()) == 5


def test_form_de_alta_tiene_prioridad_con_media_preseleccionada(client: TestClient) -> None:
    html = client.get("/").text

    assert '<option value="media" selected>' in html
    assert 'type="date" name="due_date"' in html


# --- Página: filtros y orden ---


def _ids_en_pagina(html: str) -> list[int]:
    return [int(task_id) for task_id in re.findall(r'<li[^>]*data-id="(\d+)"', html)]


def _form_filtros(html: str) -> str:
    match = re.search(r'<form class="filters".*?</form>', html, re.DOTALL)
    assert match is not None
    return match.group(0)


def test_pagina_filtra_y_ordena_igual_que_la_api(client: TestClient) -> None:
    _crear_mezcla(client)
    _crear(client, priority="media")
    query = "priority=alta&completed=false&sort=priority"

    html = client.get(f"/?{query}").text

    assert _ids_en_pagina(html) == _ids(client.get(f"/tasks?{query}"))
    assert _ids_en_pagina(client.get("/?completed=false&sort=priority").text) == _ids(
        client.get("/tasks?completed=false&sort=priority")
    )


def test_controles_muestran_los_valores_aplicados(client: TestClient) -> None:
    form = _form_filtros(client.get("/?priority=alta&completed=false&sort=priority").text)

    assert '<option value="alta" selected>' in form
    assert '<option value="false" selected>' in form
    assert '<option value="priority" selected>' in form
    assert form.count(" selected") == 3


def test_controles_en_todas_muestran_todo(client: TestClient) -> None:
    html = client.get("/?priority=&completed=&sort=").text

    assert _ids_en_pagina(html) == [1, 2, 3, 4, 5]
    assert " selected" not in _form_filtros(html)


def test_filtro_sin_coincidencias_muestra_su_mensaje(client: TestClient) -> None:
    html = client.get("/?priority=alta").text

    assert "Ninguna tarea coincide con el filtro." in html
    assert "No hay tareas todavía." not in html


def test_sin_tareas_y_sin_filtros_muestra_el_mensaje_de_siempre(client: TestClient) -> None:
    for sembrada in range(1, 6):
        client.delete(f"/tasks/{sembrada}")

    html = client.get("/").text

    assert "No hay tareas todavía." in html
    assert "Ninguna tarea coincide con el filtro." not in html


# --- Página: los filtros se mantienen después de una acción ---

_VISTA = "priority=alta&completed=false&sort=priority"


def _acciones(client: TestClient) -> list[tuple[str, dict[str, str]]]:
    completar = _crear(client, priority="alta")["id"]
    borrar = _crear(client, priority="alta")["id"]
    return [
        ("/ui/tasks", {"title": "Nueva", "priority": "baja", "due_date": ""}),
        (f"/ui/tasks/{completar}/complete", {}),
        (f"/ui/tasks/{borrar}/delete", {}),
    ]


def test_acciones_con_filtros_vuelven_a_la_misma_vista(client: TestClient) -> None:
    for url, data in _acciones(client):
        response = client.post(f"{url}?{_VISTA}", data=data, follow_redirects=False)

        assert response.status_code == 303, url
        assert response.headers["location"] == f"/?{_VISTA}", url


def test_acciones_sin_filtros_vuelven_a_la_raiz(client: TestClient) -> None:
    for url, data in _acciones(client):
        response = client.post(url, data=data, follow_redirects=False)

        assert response.status_code == 303, url
        assert response.headers["location"] == "/", url


def test_la_accion_se_aplica_aunque_lleve_filtros(client: TestClient) -> None:
    client.post(f"/ui/tasks?{_VISTA}", data={"title": "Con filtros en la URL", "priority": "baja"})

    assert (_ultima(client)["title"], _ultima(client)["priority"]) == ("Con filtros en la URL", "baja")


def test_la_pagina_con_filtros_los_pone_en_los_forms(client: TestClient) -> None:
    task_id = _crear(client, priority="alta")["id"]
    query_html = _VISTA.replace("&", "&amp;")

    html = client.get(f"/?{_VISTA}").text

    assert f'action="/ui/tasks?{query_html}"' in html
    assert f'action="/ui/tasks/{task_id}/complete?{query_html}"' in html
    assert f'action="/ui/tasks/{task_id}/delete?{query_html}"' in html


def test_la_pagina_sin_filtros_deja_los_forms_como_antes(client: TestClient) -> None:
    html = client.get("/").text

    assert 'action="/ui/tasks"' in html
    assert 'action="/ui/tasks/2/complete"' in html
    assert 'action="/ui/tasks/1/delete"' in html
