from datetime import date


def test_create_form_includes_priority_and_due_date_fields(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert 'name="prioridad"' in html
    assert 'type="date"' in html
    assert 'name="fecha_limite"' in html


def test_create_form_defaults_persist_via_api(client):
    response = client.post(
        "/ui/tasks",
        data={"title": "Desde UI", "description": "", "prioridad": "media", "fecha_limite": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303

    tasks = client.get("/tasks").json()
    created = next(task for task in tasks if task["title"] == "Desde UI")
    assert created["prioridad"] == "media"
    assert created["fecha_limite"] is None


def test_create_form_with_priority_and_date(client):
    response = client.post(
        "/ui/tasks",
        data={
            "title": "Con prioridad",
            "description": "",
            "prioridad": "alta",
            "fecha_limite": "2026-07-15",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    tasks = client.get("/tasks").json()
    created = next(task for task in tasks if task["title"] == "Con prioridad")
    assert created["prioridad"] == "alta"
    assert created["fecha_limite"] == "2026-07-15"


def test_filters_form_uses_get_and_reflected_in_url(client):
    response = client.get("/?prioridad=alta,media&vencidas=1&orden=prioridad&dir=desc")
    assert response.status_code == 200
    html = response.text
    assert 'method="get"' in html
    assert 'name="prioridad"' in html
    assert 'value="alta,media"' in html
    assert 'name="vencidas"' in html
    assert 'name="orden"' in html


def test_overdue_badge_for_pending_task(client, freeze_today):
    freeze_today(date(2026, 7, 3))
    client.post(
        "/tasks",
        json={"title": "Vencida", "prioridad": "alta", "fecha_limite": "2026-07-02"},
    )

    response = client.get("/")
    html = response.text
    assert "Vencida" in html
    assert 'class="badge badge-vencida"' in html
    assert " overdue" in html


def test_no_overdue_badge_for_today_or_completed(client, freeze_today):
    freeze_today(date(2026, 7, 3))
    client.post(
        "/tasks",
        json={"title": "Para hoy", "prioridad": "media", "fecha_limite": "2026-07-03"},
    )
    completed = client.post(
        "/tasks",
        json={"title": "Completada", "prioridad": "media", "fecha_limite": "2026-07-01"},
    ).json()
    client.patch(f"/tasks/{completed['id']}/complete")

    response = client.get("/")
    html = response.text
    assert 'class="badge badge-vencida"' not in html
    assert "Sin fecha límite" in html or "Fecha límite:" in html


def test_no_post_creation_edit_controls_for_priority_or_due_date(client):
    response = client.get("/")
    html = response.text
    assert 'name="prioridad"' in html
    assert html.count('name="fecha_limite"') == 1
