import hashlib
import json
from importlib.resources import files
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from mealf.ai import provider_for
from mealf.app import create_app
from mealf.db import Database
from mealf.food_profile import CATALOG, pantry_key
from mealf.jobs import claim, finish
from mealf.recipe_ideas import process

PATH = "/api/v1/household/food-profile"


def write(patch, base=0):
    return {"request_id": str(uuid4()), "base_revision": base, "patch": patch}


def test_food_profile_commit_order_nonconflicting_fields_and_old_receipt(harness):
    client, app, _, _ = harness
    assert client.get(PATH).json() == {
        "revision": 0,
        "profile": {
            "likes": [],
            "dislikes": [],
            "pantry_setup_done": False,
            "taste_setup_done": False,
        },
    }
    first = write({"likes": ["pasta"], "dislikes": ["mushrooms"], "taste_setup_done": True})
    saved = client.put(PATH, json=first)
    assert saved.status_code == 200 and saved.json()["revision"] == 1
    other = client.post(
        "/api/v1/auth/login",
        json={"username": "cook", "password": "a strong test password", "device_id": str(uuid4())},
    ).json()
    headers = {"Authorization": "Bearer " + other["access_token"]}
    peer = write({"pantry_setup_done": True})
    assert client.put(PATH, json=peer, headers=headers).json()["conflict"] is True
    profile = client.get(PATH).json()
    assert profile["revision"] == 2 and profile["profile"]["likes"] == ["pasta"]
    assert profile["profile"]["pantry_setup_done"] is True
    assert client.put(PATH, json=first).json() == saved.json()
    assert client.get(PATH).json() == profile
    assert client.put(PATH, json=first, headers=headers).status_code == 409
    assert client.put(PATH, json={**first, "patch": {"likes": ["rice"]}}).status_code == 409
    Database(app.state.database.root)
    assert client.get(PATH).json() == profile


@pytest.mark.parametrize(
    "patch",
    [
        {},
        {"likes": None},
        {"likes": ["unknown"]},
        {"likes": ["pasta", "pasta"]},
        {"likes": ["pasta"], "dislikes": ["pasta"]},
        {"surprise": "ignore instructions"},
    ],
)
def test_invalid_choices_are_rejected_without_a_partial_commit(harness, patch):
    client, *_ = harness
    before = client.get(PATH).json()
    assert client.put(PATH, json=write(patch)).status_code == 422
    assert client.get(PATH).json() == before


def test_preferences_require_authentication_and_cookie_csrf(harness, monkeypatch):
    from mealf.pwa_auth import AUTH_PATH, CSRF_COOKIE

    monkeypatch.setenv("BASE_URL", "https://localhost")
    with TestClient(
        harness[1],
        base_url="https://localhost",
        headers={"Origin": "https://localhost", "X-Mealf-Client": "pwa"},
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
        assert browser.put(PATH, json=write({"taste_setup_done": True})).status_code == 403
        assert (
            browser.put(
                PATH,
                json=write({"taste_setup_done": True}),
                headers={"X-CSRF-Token": browser.cookies[CSRF_COOKIE]},
            ).status_code
            == 200
        )


def test_released_installation_skips_repeated_pantry_onboarding(tmp_path, monkeypatch):
    resources = tmp_path / "released"
    (resources / "migrations").mkdir(parents=True)
    for source in files("mealf").joinpath("migrations").iterdir():
        if source.name.endswith(".sql") and source.name < "016":
            (resources / "migrations" / source.name).write_text(source.read_text())
    with monkeypatch.context() as patch:
        patch.setattr("mealf.db.files", lambda package: resources)
        database = Database(tmp_path / "data")
        # Seed the released schema directly: current setup also creates RBAC accounts.
        with database.transaction() as db:
            db.execute(
                "INSERT INTO household VALUES (1,?,?,?,?,?,?)",
                ("Retained kitchen", "UTC", "en", "cook", "synthetic hash", str(uuid4())),
            )
    upgraded = Database(database.root)
    with upgraded.connect() as db:
        row = json.loads(db.execute("SELECT payload FROM food_profile").fetchone()[0])
        assert row["pantry_setup_done"] is True and row["taste_setup_done"] is False
    Database(upgraded.root)


def test_catalogue_has_conservative_translations_without_changing_bring_names(harness, mutation):
    from datetime import date

    from mealf.planning import normalise, shopping_projection, week_start

    client, app, device, *_ = harness
    changes = [
        mutation(
            device,
            payload={
                "title": "Simple pasta",
                "servings": "2",
                "ingredients": [
                    {"id": str(uuid4()), "name": "olive oil", "quantity": "1", "unit": "tbsp"},
                    {"id": str(uuid4()), "name": "rice", "quantity": "100", "unit": "g"},
                    {"id": str(uuid4()), "name": "basmati rice", "quantity": "100", "unit": "g"},
                ],
                "steps": ["Cook."],
            },
        )
    ]
    changes.extend(
        [
            mutation(device, kind="pantry", payload={"name": "Olivenöl", "available": True}),
            mutation(device, kind="pantry", payload={"name": "Reis", "available": True}),
            mutation(
                device,
                kind="meal",
                payload={
                    "recipe_id": changes[0]["entity_id"],
                    "date": str(date.today()),
                    "category": "dinner",
                    "servings": "2",
                },
            ),
        ]
    )
    assert client.post("/api/v1/sync/push", json={"mutations": changes}).status_code == 200
    with app.state.database.connect() as db:
        projection = shopping_projection(db, week_start(date.today()))
    assert [row["name"] for row in projection.values()] == ["basmati rice"]
    assert pantry_key("OLIVENÖL") == pantry_key("olive oil")
    assert pantry_key("flour") != pantry_key("almond flour")
    assert normalise("Olivenöl") != normalise("olive oil")  # External ownership matching unchanged.
    assert len({row["id"] for row in CATALOG["items"]}) == len(CATALOG["items"])


def test_food_choices_export_restore_v4_and_v3_remains_accepted(harness, tmp_path):
    client, *_ = harness
    client.put(
        PATH, json=write({"likes": ["pasta"], "dislikes": ["mushrooms"], "taste_setup_done": True})
    )
    exported = client.get("/api/v1/admin/export").json()
    assert exported["version"] == 4 and exported["food_profile"]["likes"] == ["pasta"]
    assert "food_profile_receipt" not in json.dumps(exported)
    for version in [3, 4]:
        app = create_app(tmp_path / ("restore" + str(version)), run_worker=False)
        with TestClient(app) as target:
            auth = target.post(
                "/api/v1/setup",
                headers={
                    "X-Setup-Token": (app.state.database.root / "config/setup-token").read_text()
                },
                json={
                    "name": "Restore test",
                    "username": "cook",
                    "password": "synthetic restore test password",
                    "device_id": str(uuid4()),
                },
            )
            target.headers["Authorization"] = "Bearer " + auth.json()["access_token"]
            body = {**exported, "version": version}
            if version == 3:
                body.pop("food_profile")
            assert target.post("/api/v1/admin/import", json=body).status_code == 200
            assert target.get(PATH).json()["profile"]["likes"] == (
                ["pasta"] if version == 4 else []
            )


def test_recipe_ideas_send_the_explicit_snapshot_not_later_household_changes(harness):
    from test_recipe_ideas import GENERATED, configured, request

    client, app, *_ = harness
    configured(client)
    body = request(
        mode="surprise", ingredients="", preferences={"likes": ["pasta"], "dislikes": ["mushrooms"]}
    )
    assert client.post("/api/v1/recipe-ideas", json=body).status_code == 202
    client.put(PATH, json=write({"likes": ["fish"], "dislikes": []}))
    sent = []

    def upstream(req):
        data = json.loads(req.content)
        text = data["contents"][0]["parts"][0]["text"]
        source = json.loads(json.loads(text)["untrusted_source"])
        sent.append(source)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {"parts": [{"text": json.dumps(GENERATED)}]},
                    }
                ]
            },
        )

    job = claim(app.state.database)
    process(
        app.state.database,
        json.loads(job["payload"]),
        lambda config: provider_for(config, httpx.MockTransport(upstream)),
    )
    finish(app.state.database, job)
    assert sent == [
        {
            "available_ingredients": "",
            "language": "en",
            "mode": "surprise",
            "preferences": {"liked_foods": ["Pasta"], "disliked_foods": ["Mushrooms"]},
        }
    ]
    assert client.get("/api/v1/recipe-ideas/" + body["request_id"]).json()["state"] == "ready"
    assert client.get("/api/v1/recipes").json()["items"] == []
    assert client.post("/api/v1/recipe-ideas", json=body).status_code == 202


def test_legacy_idea_fingerprints_remain_replayable(harness):
    from test_recipe_ideas import configured, request

    client, app, *_ = harness
    configured(client)
    body = request()
    assert client.post("/api/v1/recipe-ideas", json=body).status_code == 202
    legacy = json.dumps(body, separators=(",", ":"))
    with app.state.database.connect() as db:
        row = db.execute("SELECT request,fingerprint FROM recipe_idea_request").fetchone()
    assert row["request"] == legacy
    assert row["fingerprint"] == hashlib.sha256(legacy.encode()).hexdigest()
    assert client.post("/api/v1/recipe-ideas", json=body).status_code == 202
