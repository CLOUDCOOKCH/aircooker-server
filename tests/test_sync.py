from uuid import uuid4

from fastapi.testclient import TestClient

from aircooker.app import create_app


def push(client, *mutations):
    response = client.post("/api/v1/sync/push", json={"mutations": list(mutations)})
    assert response.status_code == 200, response.text
    return response.json()


def test_duplicate_replay_and_key_reuse(harness, mutation):
    c, app, device, tokens = harness
    m = mutation(device)
    result = push(c, m)
    assert push(c, m) == result
    assert len(c.get("/api/v1/sync/pull").json()["changes"]) == 1
    m["payload"]["title"] = "Altered"
    assert c.post("/api/v1/sync/push", json={"mutations": [m]}).status_code == 409


def test_server_order_overrides_clocks_and_stale_base(harness, mutation):
    c, app, device, tokens = harness
    first = mutation(device)
    push(c, first)
    second = c.post(
        "/api/v1/auth/login",
        json={"username": "cook", "password": "a strong test password", "device_id": str(uuid4())},
    ).json()
    sessions = c.get("/api/v1/auth/sessions").json()
    other = next(s["device_id"] for s in sessions if s["id"] == second["session_id"])
    stale = mutation(
        other, entity_id=first["entity_id"], payload={"title": "Last committed", "servings": "2"}
    )
    stale["client_timestamp"] = "1990-01-01T00:00:00Z"
    response = c.post(
        "/api/v1/sync/push",
        headers={"Authorization": "Bearer " + second["access_token"]},
        json={"mutations": [stale]},
    )
    assert response.status_code == 200, response.text
    assert response.json()[0]["conflict"]
    assert (
        c.get("/api/v1/recipes/" + first["entity_id"]).json()["payload"]["title"]
        == "Last committed"
    )


def test_tombstone_rejects_offline_resurrection(harness, mutation):
    c, app, device, tokens = harness
    m = mutation(device)
    rev = push(c, m)[0]["revision"]
    deletion = mutation(device, entity_id=m["entity_id"], base=rev, operation="delete")
    push(c, deletion)
    stale = mutation(device, entity_id=m["entity_id"], base=rev)
    assert push(c, stale)[0]["status"] == "rejected_tombstone"
    assert c.get("/api/v1/recipes/" + m["entity_id"]).status_code == 404
    assert c.get("/api/v1/sync/pull").json()["changes"][-1]["deleted"]


def test_batch_atomic_and_device_boundary(harness, mutation):
    c, app, device, tokens = harness
    good = mutation(device)
    bad = mutation(device, payload={"title": ""})
    assert c.post("/api/v1/sync/push", json={"mutations": [good, bad]}).status_code == 422
    assert c.get("/api/v1/recipes").json()["items"] == []
    alien = mutation(str(uuid4()))
    assert c.post("/api/v1/sync/push", json={"mutations": [alien]}).status_code == 403


def test_delta_pagination_and_restart(harness, mutation, tmp_path):
    c, app, device, tokens = harness
    push(c, *[mutation(device) for _ in range(3)])
    page = c.get("/api/v1/sync/pull?limit=2").json()
    assert len(page["changes"]) == 2 and page["has_more"]
    app2 = create_app(tmp_path, False)
    with TestClient(app2) as other:
        other.headers.update(c.headers)
        last = other.get("/api/v1/sync/pull", params={"cursor": page["cursor"]}).json()
        assert len(last["changes"]) == 1 and not last["has_more"]
        assert other.get("/api/v1/sync/pull?cursor=999").status_code == 409
