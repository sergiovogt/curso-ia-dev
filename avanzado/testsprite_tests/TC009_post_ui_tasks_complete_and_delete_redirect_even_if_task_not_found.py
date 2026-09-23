import requests
import sys

BASE_URL = "http://localhost:8010"
TIMEOUT = 30


def test_tc009_post_ui_tasks_complete_and_delete_redirect_even_if_task_not_found():
    # Use a clearly non-existent id for the "not found" checks
    nonexistent_id = 999999

    # Endpoints for UI actions (form posts)
    complete_ui_url_nonexistent = f"{BASE_URL}/ui/tasks/{nonexistent_id}/complete"
    delete_ui_url_nonexistent = f"{BASE_URL}/ui/tasks/{nonexistent_id}/delete"

    # 1) Verify POST /ui/tasks/{id}/complete returns 303 and Location "/" even if id not found
    try:
        resp = requests.post(complete_ui_url_nonexistent, data={}, allow_redirects=False, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"HTTP request failed for complete (nonexistent): {e}"
    assert resp.status_code == 303, f"expected 303 for complete (nonexistent), got {resp.status_code}"
    location = resp.headers.get("Location")
    assert location == "/", f'expected Location header "/" for complete (nonexistent), got {location}'

    # 2) Verify POST /ui/tasks/{id}/delete returns 303 and Location "/" even if id not found
    try:
        resp = requests.post(delete_ui_url_nonexistent, data={}, allow_redirects=False, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"HTTP request failed for delete (nonexistent): {e}"
    assert resp.status_code == 303, f"expected 303 for delete (nonexistent), got {resp.status_code}"
    location = resp.headers.get("Location")
    assert location == "/", f'expected Location header "/" for delete (nonexistent), got {location}'

    # 3) Additionally test the behavior for an existing task id:
    created_task_id = None
    try:
        # Create a new task via API JSON to obtain a valid id
        create_url = f"{BASE_URL}/tasks"
        payload = {"title": "tc009 temporary task"}
        try:
            create_resp = requests.post(create_url, json=payload, timeout=TIMEOUT)
        except requests.RequestException as e:
            assert False, f"HTTP request failed creating task: {e}"

        assert create_resp.status_code == 201, f"expected 201 when creating task, got {create_resp.status_code}"
        try:
            created = create_resp.json()
        except ValueError:
            assert False, "Create task response is not valid JSON"
        created_task_id = created.get("id")
        assert isinstance(created_task_id, int), f"created task id should be int, got {created_task_id!r}"

        # POST to /ui/tasks/{id}/complete for existing id -> should 303 Location "/"
        complete_ui_url = f"{BASE_URL}/ui/tasks/{created_task_id}/complete"
        try:
            resp = requests.post(complete_ui_url, data={}, allow_redirects=False, timeout=TIMEOUT)
        except requests.RequestException as e:
            assert False, f"HTTP request failed for complete (existing): {e}"
        assert resp.status_code == 303, f"expected 303 for complete (existing), got {resp.status_code}"
        location = resp.headers.get("Location")
        assert location == "/", f'expected Location header "/" for complete (existing), got {location}'

        # POST to /ui/tasks/{id}/delete for existing id -> should 303 Location "/"
        delete_ui_url = f"{BASE_URL}/ui/tasks/{created_task_id}/delete"
        try:
            resp = requests.post(delete_ui_url, data={}, allow_redirects=False, timeout=TIMEOUT)
        except requests.RequestException as e:
            assert False, f"HTTP request failed for delete (existing): {e}"
        assert resp.status_code == 303, f"expected 303 for delete (existing), got {resp.status_code}"
        location = resp.headers.get("Location")
        assert location == "/", f'expected Location header "/" for delete (existing), got {location}'

    finally:
        # Cleanup: ensure the created task is removed. DELETE /tasks/{id} may return 204 or 404 (if already deleted).
        if created_task_id is not None:
            delete_api_url = f"{BASE_URL}/tasks/{created_task_id}"
            try:
                cleanup_resp = requests.delete(delete_api_url, timeout=TIMEOUT)
                assert cleanup_resp.status_code in (204, 404), (
                    f"cleanup DELETE expected 204 or 404, got {cleanup_resp.status_code}"
                )
            except requests.RequestException as e:
                # If cleanup fails at network level, surface as test failure
                assert False, f"HTTP request failed during cleanup delete: {e}"


if __name__ == "__main__":
    try:
        test_tc009_post_ui_tasks_complete_and_delete_redirect_even_if_task_not_found()
    except AssertionError as e:
        print("TEST FAILED:", e)
        sys.exit(1)
    print("TEST PASSED")
    sys.exit(0)