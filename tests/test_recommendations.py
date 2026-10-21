from datetime import date
from uuid import uuid4

import pytest

from aircooker.recommendations import suggest_week


def commit(c, m):
    response = c.post("/api/v1/sync/push", json={"mutations": [m]})
    assert response.status_code == 200, response.text
    return response.json()[0]


def library(c, device, mutation):
    recipes = []
    for title, rating in [("Soup", 5), ("Rice", 4), ("Pasta", 3)]:
        recipe = mutation(device, payload={"title": title, "servings": "2", "rating": rating})
        commit(c, recipe)
        recipes.append(recipe["entity_id"])
    return recipes


def leftover_setup(harness, mutation):
    c, app, device, _ = harness
    rid = library(c, device, mutation)[0]
    leftover = mutation(
        device,
        kind="leftover",
        payload={"recipe_id": rid, "portions": "4", "produced_on": "2026-10-19"},
    )
    version = commit(c, leftover)["revision"]
    meal = mutation(
        device,
        kind="meal",
        payload={
            "recipe_id": rid,
            "leftover_id": leftover["entity_id"],
            "date": "2026-10-20",
            "category": "dinner",
            "servings": "2",
        },
    )
    meal_version = commit(c, meal)["revision"]
    return leftover, version, meal, meal_version


@pytest.mark.parametrize(
    "change,code",
    [
        ({"portions": "1.5"}, "insufficient_leftover_portions"),
        ({"produced_on": "2026-10-21"}, "leftover_produced_after_booking"),
    ],
)
def test_editing_leftovers_cannot_invalidate_bookings(harness, mutation, change, code):
    c, _, device, _ = harness
    leftover, version, _, _ = leftover_setup(harness, mutation)
    edit = mutation(
        device,
        kind="leftover",
        entity_id=leftover["entity_id"],
        base=version,
        payload={**leftover["payload"], **change},
    )
    response = c.post("/api/v1/sync/push", json={"mutations": [edit]})
    assert response.status_code == 409 and response.json()["error"]["code"] == code
    assert c.get("/api/v1/leftovers/" + leftover["entity_id"]).json()["revision"] == version


def test_leftover_recipe_change_and_deletion_require_releasing_bookings(harness, mutation):
    c, _, device, _ = harness
    leftover, version, _, _ = leftover_setup(harness, mutation)
    other = mutation(device)
    commit(c, other)
    for operation, payload, code in [
        (
            "upsert",
            {**leftover["payload"], "recipe_id": other["entity_id"]},
            "leftover_recipe_in_use",
        ),
        ("delete", None, "leftover_in_use"),
    ]:
        response = c.post(
            "/api/v1/sync/push",
            json={
                "mutations": [
                    mutation(
                        device,
                        kind="leftover",
                        entity_id=leftover["entity_id"],
                        base=version,
                        payload=payload,
                        operation=operation,
                    )
                ]
            },
        )
        assert response.status_code == 409 and response.json()["error"]["code"] == code


def test_discarding_unallocated_portions_preserves_existing_booking(harness, mutation):
    c, _, device, _ = harness
    leftover, version, meal, meal_version = leftover_setup(harness, mutation)
    commit(
        c,
        mutation(
            device,
            kind="leftover",
            entity_id=leftover["entity_id"],
            base=version,
            payload={**leftover["payload"], "discarded": True},
        ),
    )
    commit(
        c,
        mutation(
            device,
            kind="meal",
            entity_id=meal["entity_id"],
            base=meal_version,
            payload={**meal["payload"], "cooked": True},
        ),
    )
    new = mutation(device, kind="meal", payload={**meal["payload"], "servings": "1"})
    assert c.post("/api/v1/sync/push", json={"mutations": [new]}).status_code == 409


def test_suggestions_use_leftovers_without_spending_reserved_portions(harness, mutation):
    c, _, _, _ = harness
    leftover, _, _, _ = leftover_setup(harness, mutation)
    before = c.get("/api/v1/calendar/meals").json()
    preview = c.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()
    reused = [m for m in preview["meals"] if m["leftover_id"]]
    assert len(reused) == 1 and reused[0]["leftover_id"] == leftover["entity_id"]
    assert reused[0]["reasons"] == ["use_available_leftovers"]
    assert all(m["date"] != "2026-10-20" for m in preview["meals"])
    assert c.get("/api/v1/calendar/meals").json() == before


def test_history_ratings_variety_and_explicit_repetition(harness, mutation):
    c, app, device, _ = harness
    ids = library(c, device, mutation)
    commit(
        c,
        mutation(
            device,
            kind="meal",
            payload={
                "recipe_id": ids[0],
                "date": "2026-10-18",
                "category": "dinner",
                "cooked": True,
            },
        ),
    )
    with app.state.database.connect() as db:
        suggestions = suggest_week(db, date(2026, 10, 19))
        assert suggestions[0]["recipe_id"] != ids[0]
        assert len(suggestions) == 3 and len({m["recipe_id"] for m in suggestions}) == 3
        repeated = suggest_week(db, date(2026, 10, 19), allow_repeats=True)
        assert len(repeated) == 7 and len({m["recipe_id"] for m in repeated[:3]}) == 3
        all_slots = suggest_week(
            db, date(2026, 10, 19), categories=("breakfast", "lunch"), allow_repeats=True
        )
        assert len(all_slots) == 14 and {m["category"] for m in all_slots} == {"breakfast", "lunch"}


def test_approve_preview_is_atomic_idempotent_and_survives_app_restart(harness, mutation):
    c, app, device, _ = harness
    library(c, device, mutation)
    preview = c.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()
    changes = [
        mutation(device, kind="meal", payload={k: v for k, v in m.items() if k != "reasons"})
        for m in preview["meals"]
    ]
    body = {
        "request_id": str(uuid4()),
        "monday": preview["monday"],
        "basis": preview["basis"],
        "mutations": changes,
    }
    first = c.post("/api/v1/suggestions/apply", json=body)
    assert first.status_code == 200, first.text
    assert c.post("/api/v1/suggestions/apply", json=body).json() == first.json()
    from aircooker.db import Database
    from aircooker.models import SuggestionApply
    from aircooker.suggestion_apply import apply_preview

    assert (
        apply_preview(
            Database(app.state.database.root), SuggestionApply.model_validate(body), device
        )
        == first.json()
    )
    changed = {**body, "mutations": changes[:1]}
    assert c.post("/api/v1/suggestions/apply", json=changed).status_code == 409
    assert len(c.get("/api/v1/calendar/meals").json()["items"]) == len(changes)


def test_stale_or_partially_invalid_preview_does_not_modify_plan(harness, mutation):
    c, app, device, _ = harness
    ids = library(c, device, mutation)
    preview = c.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()
    first = mutation(
        device,
        kind="meal",
        payload={"recipe_id": ids[0], "date": "2026-10-19", "category": "dinner"},
    )
    bad = mutation(
        device,
        kind="meal",
        payload={"recipe_id": str(uuid4()), "date": "2026-10-20", "category": "dinner"},
    )
    body = {
        "request_id": str(uuid4()),
        "monday": preview["monday"],
        "basis": preview["basis"],
        "mutations": [first, bad],
    }
    assert c.post("/api/v1/suggestions/apply", json=body).status_code == 409
    assert not c.get("/api/v1/calendar/meals").json()["items"]
    with app.state.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM suggestion_application").fetchone()[0] == 0
    commit(c, first)
    response = c.post(
        "/api/v1/suggestions/apply", json={**body, "request_id": str(uuid4()), "mutations": [bad]}
    )
    assert (
        response.status_code == 409
        and response.json()["error"]["code"] == "suggestion_preview_stale"
    )


def test_canonical_offline_recommendation_fixture(tmp_path):
    import json
    from decimal import Decimal
    from pathlib import Path

    from aircooker.db import Database

    fixture = json.loads(Path("contracts/fixtures/recommendations-v1.json").read_text())
    database = Database(tmp_path)
    with database.transaction() as db:
        for row in fixture["rows"]:
            db.execute(
                "INSERT INTO entity VALUES (?,?,?,?,?,?)",
                (
                    row["kind"],
                    row["id"],
                    row["revision"],
                    0,
                    json.dumps(row["payload"]),
                    "2026-10-20T00:00:00Z",
                ),
            )
        for case in fixture["cases"]:
            actual = suggest_week(
                db,
                date.fromisoformat(fixture["week"]),
                case["seed"],
                case["categories"],
                case["allow_repeats"],
                None if case["servings"] is None else Decimal(case["servings"]),
            )
            assert actual == case["expected"]


def test_two_devices_cannot_reserve_same_last_portions(harness, mutation):
    from concurrent.futures import ThreadPoolExecutor

    c, app, device, _ = harness
    rid = library(c, device, mutation)[0]
    leftover = mutation(
        device,
        kind="leftover",
        payload={"recipe_id": rid, "portions": "2", "produced_on": "2026-10-19"},
    )
    commit(c, leftover)
    other_device = str(uuid4())
    session = c.post(
        "/api/v1/auth/login",
        json={"username": "cook", "password": "a strong test password", "device_id": other_device},
    ).json()
    payload = {
        "recipe_id": rid,
        "leftover_id": leftover["entity_id"],
        "date": "2026-10-20",
        "category": "dinner",
        "servings": "2",
    }

    def reserve(pair):
        dev, headers = pair
        return c.post(
            "/api/v1/sync/push",
            json={"mutations": [mutation(dev, kind="meal", payload=payload)]},
            headers=headers,
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                reserve,
                [
                    (device, {}),
                    (other_device, {"Authorization": "Bearer " + session["access_token"]}),
                ],
            )
        )
    assert sorted(results) == [200, 409]
    assert len(c.get("/api/v1/calendar/meals").json()["items"]) == 1


@pytest.mark.parametrize("existing", [False, True])
def test_approval_never_replaces_occupied_slots(harness, mutation, existing):
    c, _, device, _ = harness
    rid = library(c, device, mutation)[0]
    payload = {"recipe_id": rid, "date": "2026-10-19", "category": "dinner", "servings": "2"}
    if existing:
        commit(c, mutation(device, kind="meal", payload=payload))
    preview = c.post("/api/v1/suggestions/weekly?monday=2026-10-19").json()
    changes = [mutation(device, kind="meal", payload=payload)]
    if not existing:
        changes.append(mutation(device, kind="meal", payload=payload))
    before = c.get("/api/v1/calendar/meals").json()
    response = c.post(
        "/api/v1/suggestions/apply",
        json={
            "request_id": str(uuid4()),
            "monday": preview["monday"],
            "basis": preview["basis"],
            "mutations": changes,
        },
    )
    assert (
        response.status_code == 409
        and response.json()["error"]["code"] == "suggestion_slot_occupied"
    )
    assert c.get("/api/v1/calendar/meals").json() == before


def test_repetition_waits_for_all_available_recipes_despite_extreme_ratings(harness, mutation):
    c, app, device, _ = harness
    ids = []
    for index, rating in enumerate([1, 5, 5]):
        recipe = mutation(
            device, payload={"title": f"Recipe {index}", "servings": "2", "rating": rating}
        )
        commit(c, recipe)
        ids.append(recipe["entity_id"])
    commit(
        c,
        mutation(
            device,
            kind="meal",
            payload={
                "recipe_id": ids[0],
                "date": "2026-10-18",
                "category": "dinner",
                "cooked": True,
            },
        ),
    )
    with app.state.database.connect() as db:
        for seed in range(10):
            suggestions = suggest_week(db, date(2026, 10, 19), seed=seed, allow_repeats=True)
            assert len(suggestions) == 7
            assert len({meal["recipe_id"] for meal in suggestions[:3]}) == 3
            assert len({meal["recipe_id"] for meal in suggestions[3:6]}) == 3
