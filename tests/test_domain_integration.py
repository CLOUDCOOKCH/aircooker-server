from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from mealf.app import create_app
from mealf.planning import shopping_projection


def commit(c, m):
    response = c.post("/api/v1/sync/push", json={"mutations": [m]})
    assert response.status_code == 200, response.text
    return response.json()[0]


def test_projection_units_pantry_leftovers_and_recurrence(harness, mutation):
    c, app, device, tokens = harness
    flour = str(uuid4())
    oil = str(uuid4())
    salt = str(uuid4())
    recipe = mutation(
        device,
        payload={
            "title": "Bread",
            "servings": "2",
            "ingredients": [
                {"id": flour, "name": "Flour", "quantity": "0.2", "unit": "kg"},
                {"id": oil, "name": "Oil", "quantity": "50", "unit": "ml"},
                {"id": salt, "name": "Salt", "quantity": None, "original_text": "to taste"},
            ],
        },
    )
    commit(c, recipe)
    commit(c, mutation(device, kind="pantry", payload={"name": " SALT ", "available": True}))
    meal = {
        "recipe_id": recipe["entity_id"],
        "date": "2026-10-19",
        "category": "dinner",
        "servings": "4",
    }
    commit(c, mutation(device, kind="meal", payload=meal))
    commit(
        c, mutation(device, kind="meal", payload={**meal, "date": "2026-10-20", "servings": "2"})
    )
    leftover = mutation(
        device,
        kind="leftover",
        payload={"recipe_id": recipe["entity_id"], "portions": "2", "produced_on": "2026-10-19"},
    )
    commit(c, leftover)
    commit(
        c,
        mutation(
            device,
            kind="meal",
            payload={
                **meal,
                "date": "2026-10-21",
                "servings": "2",
                "leftover_id": leftover["entity_id"],
            },
        ),
    )
    with app.state.database.connect() as db:
        projection = list(shopping_projection(db, date(2026, 10, 19)).values())
        assert len(projection) == 2
        flour = next(i for i in projection if i["name"] == "Flour")
        assert flour["spec"] == "600 g"
        assert next(i for i in projection if i["name"] == "Oil")["spec"] == "150 ml"
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        assert db.execute("SELECT COUNT(*) FROM recipe_ingredient").fetchone()[0] == 3


def test_no_overallocation_of_leftovers(harness, mutation):
    c, app, device, tokens = harness
    recipe = mutation(device)
    commit(c, recipe)
    leftover = mutation(
        device,
        kind="leftover",
        payload={"recipe_id": recipe["entity_id"], "portions": "2", "produced_on": "2026-10-19"},
    )
    commit(c, leftover)
    payload = {
        "recipe_id": recipe["entity_id"],
        "date": "2026-10-19",
        "category": "dinner",
        "servings": "2",
        "leftover_id": leftover["entity_id"],
    }
    first = mutation(device, kind="meal", payload=payload)
    revision = commit(c, first)["revision"]
    second = mutation(device, kind="meal", payload=payload)
    assert c.post("/api/v1/sync/push", json={"mutations": [second]}).status_code == 409
    commit(
        c,
        mutation(
            device,
            kind="meal",
            entity_id=first["entity_id"],
            base=revision,
            payload={**payload, "date": "2026-10-20"},
        ),
    )


def test_suggestions_are_deterministic_preview(harness, mutation):
    c, app, device, tokens = harness
    for title in ["Soup", "Rice", "Pasta"]:
        commit(c, mutation(device, payload={"title": title, "servings": "2", "rating": 5}))
    before = c.get("/api/v1/calendar/meals").json()
    first = c.post("/api/v1/suggestions/weekly?monday=2026-10-19&seed=1").json()
    second = c.post("/api/v1/suggestions/weekly?monday=2026-10-19&seed=1").json()
    assert first == second and first["preview"]
    assert len({i["recipe_id"] for i in first["meals"][:3]}) == 3
    assert c.get("/api/v1/calendar/meals").json() == before


def test_export_restore_clean_household_and_duplicate_rollback(harness, mutation, tmp_path):
    c, app, device, tokens = harness
    recipe = mutation(device)
    commit(c, recipe)
    commit(
        c,
        mutation(
            device,
            kind="meal",
            payload={
                "recipe_id": recipe["entity_id"],
                "date": "2026-10-19",
                "category": "dinner",
                "servings": "2",
            },
        ),
    )
    exported = c.get("/api/v1/admin/export")
    assert exported.status_code == 200
    for secret in ["access_token", "refresh_token", "password_hash", "a strong test password"]:
        assert secret not in exported.text
    target = create_app(tmp_path / "restored", False)
    with TestClient(target) as other:
        setup_token = (tmp_path / "restored" / "config" / "setup-token").read_text()
        setup = other.post(
            "/api/v1/setup",
            headers={"X-Setup-Token": setup_token},
            json={
                "name": "Restored",
                "username": "cook",
                "password": "new strong password",
                "device_id": str(uuid4()),
            },
        )
        other.headers["Authorization"] = "Bearer " + setup.json()["access_token"]
        response = other.post("/api/v1/admin/import", json=exported.json())
        assert response.status_code == 200, response.text
        assert response.json()["imported"] == 2
        assert other.get("/api/v1/recipes").json()["items"][0]["payload"]["title"] == "Soup"
        assert other.post("/api/v1/admin/import", json=exported.json()).status_code == 409
        assert len(other.get("/api/v1/recipes").json()["items"]) == 1


def test_browser_session_cookie_and_csrf(harness):
    c, app, device, tokens = harness
    with TestClient(app, base_url="https://localhost") as browser:
        body = {"username": "cook", "password": "a strong test password", "device_id": str(uuid4())}
        assert (
            browser.post(
                "/api/v1/admin/login", json=body, headers={"Origin": "https://evil.example"}
            ).status_code
            == 403
        )
        response = browser.post(
            "/api/v1/admin/login", json=body, headers={"Origin": "https://localhost"}
        )
        assert response.status_code == 200, response.text
        assert "access_token" not in response.text and "HttpOnly" in response.headers["set-cookie"]
        assert browser.get("/api/v1/admin/jobs").status_code == 200
        assert (
            browser.post(
                "/api/v1/admin/logout", headers={"Origin": "https://localhost"}
            ).status_code
            == 403
        )
        assert (
            browser.post(
                "/api/v1/admin/logout",
                headers={
                    "Origin": "https://localhost",
                    "X-CSRF-Token": browser.cookies["mealf_csrf"],
                },
            ).status_code
            == 204
        )
        assert browser.get("/api/v1/admin/jobs").status_code == 401
