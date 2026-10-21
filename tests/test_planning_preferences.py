import json
from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from aircooker.app import create_app
from aircooker.db import Database
from aircooker.models import SuggestionApply
from aircooker.planning_preferences import context
from aircooker.recommendations import suggest_week
from aircooker.suggestion_apply import apply_preview

PATH = "/api/v1/household/planning-preferences"


def request(preferences, base=0):
    return {"request_id": str(uuid4()), "base_revision": base, "preferences": preferences}


def recipe(client, device, mutation):
    change = mutation(device, payload={"title": "Soup", "servings": "2"})
    response = client.post("/api/v1/sync/push", json={"mutations": [change]})
    assert response.status_code == 200, response.text
    return change["entity_id"]


def clean_client(root):
    app = create_app(root, run_worker=False)
    client = TestClient(app)
    body = {
        "name": "Restored kitchen",
        "username": "cook",
        "password": "synthetic restored kitchen password",
        "device_id": str(uuid4()),
    }
    response = client.post(
        "/api/v1/setup",
        json=body,
        headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
    )
    assert response.status_code == 201, response.text
    client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
    return client, app


def test_preferences_use_server_commit_order_and_old_replay_cannot_overwrite_a_peer(harness):
    client, app, device, _ = harness
    first = request({"categories": ["dinner", "breakfast"], "servings": "3.5"})
    accepted = client.put(PATH, json=first)
    assert accepted.status_code == 200 and accepted.json()["revision"] == 1
    other = client.post(
        "/api/v1/auth/login",
        json={"username": "cook", "password": "a strong test password", "device_id": str(uuid4())},
    ).json()
    headers = {"Authorization": "Bearer " + other["access_token"]}
    second = request({"categories": ["lunch"], "allow_repeats": True}, base=0)
    saved = client.put(PATH, json=second, headers=headers)
    assert saved.status_code == 200 and saved.json() == {
        "request_id": second["request_id"],
        "revision": 2,
        "conflict": True,
    }
    assert client.put(PATH, json=first).json() == accepted.json()
    assert client.get(PATH).json()["preferences"]["categories"] == ["lunch"]
    assert client.put(PATH, json={**first, "preferences": {"servings": "4"}}).status_code == 409
    assert client.put(PATH, json=first, headers=headers).status_code == 409
    with Database(app.state.database.root).connect() as db:
        assert context(db).revision == 2 and context(db).preferences.allow_repeats
    for invalid in (
        {"categories": []},
        {"categories": ["dinner", "dinner"]},
        {"servings": "0"},
        {"servings": "101"},
    ):
        assert client.put(PATH, json=request(invalid)).status_code == 422
    assert client.get(PATH).json()["revision"] == 2


def test_household_defaults_drive_previews_with_explicit_legacy_query_overrides(harness, mutation):
    client, _, device, _ = harness
    recipe(client, device, mutation)
    assert (
        client.put(
            PATH,
            json=request(
                {
                    "categories": ["breakfast", "lunch"],
                    "allow_repeats": True,
                    "servings": "3.5",
                    "use_leftovers": False,
                }
            ),
        ).status_code
        == 200
    )
    preview = client.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()
    assert len(preview["meals"]) == 14
    assert {item["category"] for item in preview["meals"]} == {"breakfast", "lunch"}
    assert {item["servings"] for item in preview["meals"]} == {"3.5"}
    override = client.post(
        "/api/v1/suggestions/weekly?monday=2026-10-19&categories=dinner&allow_repeats=false&servings=2"
    ).json()
    assert len(override["meals"]) == 1 and override["meals"][0]["category"] == "dinner"
    assert not client.get("/api/v1/calendar/meals").json()["items"]


def test_acceptance_learning_is_atomic_once_per_recipe_per_approval_and_survives_restart(
    harness, mutation
):
    client, app, device, _ = harness
    rid = recipe(client, device, mutation)
    changes = [
        mutation(device, kind="meal", payload={"recipe_id": rid, "date": day, "category": "dinner"})
        for day in ("2026-10-19", "2026-10-20")
    ]
    body = {"request_id": str(uuid4()), "monday": "2026-10-19", "basis": None, "mutations": changes}
    accepted = client.post("/api/v1/suggestions/apply", json=body)
    assert accepted.status_code == 200, accepted.text
    assert client.post("/api/v1/suggestions/apply", json=body).json() == accepted.json()
    restarted = Database(app.state.database.root)
    assert apply_preview(restarted, SuggestionApply.model_validate(body), device) == accepted.json()
    assert client.get(PATH).json()["accepted_counts"] == {rid: 1}
    # Rejected occupied-slot approvals do not teach or partially create meals.
    assert (
        client.post(
            "/api/v1/suggestions/apply",
            json={
                **body,
                "request_id": str(uuid4()),
                "mutations": [mutation(device, kind="meal", payload=changes[0]["payload"])],
            },
        ).status_code
        == 409
    )
    assert client.get(PATH).json()["accepted_counts"] == {rid: 1}
    future = client.post("/api/v1/suggestions/weekly?monday=2026-11-02").json()
    assert "previously_accepted" in future["meals"][0]["reasons"]
    assert all(not item["cooked"] for item in future["meals"])


def test_learning_never_overrides_variety_and_preview_basis_tracks_preferences(harness, mutation):
    client, app, device, _ = harness
    ids = [recipe(client, device, mutation) for _ in range(3)]
    prior = client.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()
    with app.state.database.transaction() as db:
        db.execute("INSERT INTO suggestion_acceptance VALUES (?,1000000)", (ids[0],))
        result = suggest_week(db, date(2026, 10, 19), allow_repeats=True)
        assert result[0]["recipe_id"] == ids[0]
        assert len({item["recipe_id"] for item in result[:3]}) == 3
        assert len({item["recipe_id"] for item in result[3:6]}) == 3
    changed = client.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()
    assert changed["basis"] != prior["basis"]
    client.put(PATH, json=request({"use_leftovers": False}))
    assert (
        client.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()["basis"]
        != changed["basis"]
    )


def test_json_export_restore_includes_nonsecret_preferences_and_learning_atomically(
    harness, mutation, tmp_path
):
    client, app, device, _ = harness
    rid = recipe(client, device, mutation)
    client.put(PATH, json=request({"categories": ["lunch"], "servings": "4"}))
    with app.state.database.transaction() as db:
        db.execute("INSERT INTO suggestion_acceptance VALUES (?,3)", (rid,))
    exported = client.get("/api/v1/admin/export").json()
    assert exported["version"] == 3 and exported["accepted_suggestions"] == {rid: 3}
    restored, other = clean_client(tmp_path / "clean")
    response = restored.post("/api/v1/admin/import", json=exported)
    assert response.status_code == 200, response.text
    state = restored.get(PATH).json()
    assert state["preferences"]["servings"] == "4" and state["accepted_counts"] == {rid: 3}
    assert "planning_preference_receipt" not in json.dumps(exported)
    failed, failed_app = clean_client(tmp_path / "failed")
    invalid = {**exported, "accepted_suggestions": {str(uuid4()): 3}}
    assert failed.post("/api/v1/admin/import", json=invalid).status_code == 422
    assert not failed.get("/api/v1/recipes").json()["items"]
    assert failed.get(PATH).json()["revision"] == 0
    legacy = {
        key: value
        for key, value in exported.items()
        if key not in ("planning_preferences", "accepted_suggestions")
    }
    legacy["version"] = 2
    assert failed.post("/api/v1/admin/import", json=legacy).status_code == 200
    assert failed.get(PATH).json()["preferences"]["categories"] == ["dinner"]
    restored.close()
    failed.close()


def test_preferences_require_authentication_and_cookie_csrf(harness, monkeypatch):
    from aircooker.pwa_auth import AUTH_PATH, CSRF_COOKIE

    monkeypatch.setenv("BASE_URL", "https://localhost")
    with TestClient(
        harness[1],
        base_url="https://localhost",
        headers={"Origin": "https://localhost", "X-Aircooker-Client": "pwa"},
    ) as browser:
        assert browser.get(PATH).status_code == 401
        assert (
            browser.post(
                AUTH_PATH + "/login",
                json={
                    "username": "cook",
                    "password": "a strong test password",
                    "device_id": str(uuid4()),
                },
            ).status_code
            == 200
        )
        body = request({"allow_repeats": True})
        assert browser.put(PATH, json=body).status_code == 403
        assert (
            browser.put(
                PATH, json=body, headers={"X-CSRF-Token": browser.cookies.get(CSRF_COOKIE)}
            ).status_code
            == 200
        )


def test_leftover_preference_changes_actual_candidates_without_changing_inventory(
    harness, mutation
):
    client, _, device, _ = harness
    rid = recipe(client, device, mutation)
    leftover = mutation(
        device,
        kind="leftover",
        payload={"recipe_id": rid, "portions": "2", "produced_on": "2026-10-19"},
    )
    assert client.post("/api/v1/sync/push", json={"mutations": [leftover]}).status_code == 200
    first = client.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()
    assert first["meals"][0]["leftover_id"] == leftover["entity_id"]
    assert client.put(PATH, json=request({"use_leftovers": False})).status_code == 200
    next_preview = client.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()
    assert all(item["leftover_id"] is None for item in next_preview["meals"])
    assert (
        client.get("/api/v1/leftovers/" + leftover["entity_id"]).json()["payload"]["portions"]
        == "2"
    )
