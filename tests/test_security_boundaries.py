"""Regression tests for login admission and bounded recipe quantity expansion."""

import json
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter, ValidationError

from mealf.models import Ingredient, Leftover, Meal, Positive, Recipe, TemplateSlot
from mealf.planning import shopping_projection
from mealf.planning_preferences import PlanningPreferences
from mealf.quantities import bounded_amount, fixed_amount
from mealf.recipe_extraction import Amount
from mealf.recipe_ideas import IdeaIngredient, RecipeIdea


@pytest.mark.parametrize("path", ["auth/login", "admin/login", "pwa/auth/login"])
def test_ip_blocked_requests_do_not_exhaust_other_devices(harness, monkeypatch, path):
    _, app, device, _ = harness
    monkeypatch.setenv("BASE_URL", "https://testserver")
    attacker = TestClient(app, base_url="https://testserver", client=("198.51.100.10", 1234))
    body = {"username": "unknown", "password": "wrong", "device_id": device}
    for attempt in range(40):
        response = attacker.post(
            "/api/v1/" + path, json=body, headers={"Origin": "https://testserver"}
        )
        assert response.status_code == (401 if attempt < 10 else 429)
    with app.state.database.connect() as db:
        assert (
            db.execute("SELECT count FROM rate_limit WHERE key='login:household'").fetchone()[0]
            == 10
        )
        assert (
            db.execute("SELECT count FROM rate_limit WHERE key='login:198.51.100.10'").fetchone()[0]
            == 40
        )
    fresh = TestClient(app, base_url="https://testserver", client=("203.0.113.20", 1234))
    assert (
        fresh.post(
            "/api/v1/" + path,
            json={**body, "username": "cook", "password": "a strong test password"},
            headers={"Origin": "https://testserver"},
        ).status_code
        == 200
    )


def test_distributed_login_limit_and_expiry_remain(harness):
    _, app, device, _ = harness
    body = {"username": "unknown", "password": "wrong", "device_id": device}
    for source in range(3):
        client = TestClient(app, client=(f"198.51.100.{source + 1}", 1234))
        for _ in range(10):
            assert client.post("/api/v1/auth/login", json=body).status_code == 401
    fresh = TestClient(app, client=("203.0.113.20", 1234))
    valid = {**body, "username": "cook", "password": "a strong test password"}
    assert fresh.post("/api/v1/auth/login", json=valid).status_code == 429
    with app.state.database.transaction() as db:
        db.execute("UPDATE rate_limit SET resets=0")
    assert fresh.post("/api/v1/auth/login", json=valid).status_code == 200


@pytest.mark.parametrize(
    "value", ["1e-1000000", "10e-1000001", "0.1E-999999", "1e-1000000000", "0." + "0" * 99 + "1"]
)
def test_decimal_siblings_reject_expansion(value):
    rid = uuid4()
    models = [
        (Ingredient, {"id": uuid4(), "name": "Flour", "quantity": value}),
        (Ingredient, {"id": uuid4(), "name": "Flour", "quantity": "0", "quantity_max": value}),
        (Recipe, {"title": "Bread", "servings": value}),
        (Meal, {"recipe_id": rid, "date": "2026-10-19", "category": "dinner", "servings": value}),
        (Leftover, {"recipe_id": rid, "produced_on": "2026-10-19", "portions": value}),
        (TemplateSlot, {"recipe_id": rid, "weekday": 0, "category": "dinner", "servings": value}),
        (PlanningPreferences, {"servings": value}),
        (IdeaIngredient, {"name": "Flour", "quantity": value}),
        (
            RecipeIdea,
            {
                "title": "Bread",
                "servings": value,
                "ingredients": [{"name": "Flour"}],
                "steps": ["Bake"],
            },
        ),
    ]
    for model, data in models:
        with pytest.raises(ValidationError):
            model.model_validate(data)
    if "e" in value.lower():
        with pytest.raises(ValueError):
            fixed_amount(Decimal(value))


def test_numeric_controls_preserve_representation_and_precision():
    adapter = TypeAdapter(Positive)
    for text in ["1.00", "1e-3", "1e-98", "10e-99", "0.3333333333333333333333333333", "1000000"]:
        original = Decimal(text)
        assert str(adapter.validate_python(original)) == str(original)
        assert Decimal(fixed_amount(original)) == original
    long = Decimal("0." + "1234567890" * 9)
    assert Decimal(fixed_amount(long)) == long  # No context-precision rounding.
    for text in ["0E-1000000000", "0.00"]:
        original = Decimal(text)
        assert str(bounded_amount(original)) == str(original)
        assert fixed_amount(original) == "0"
    with pytest.raises(ValidationError):
        adapter.validate_python("1e-99")  # 101 fixed characters.
    for value in [5e-324, 1e-308]:
        with pytest.raises(ValidationError):
            TypeAdapter(Amount).validate_python(value)
    assert TypeAdapter(Amount).validate_python(0.001) == 0.001
    assert fixed_amount(Decimal("1e-202")) == "0." + "0" * 201 + "1"


def test_rejected_sync_and_query_keep_data_and_replay(harness, mutation):
    client, app, device, _ = harness
    body = mutation(
        device,
        payload={
            "title": "Bread",
            "servings": "1.00",
            "ingredients": [{"id": str(uuid4()), "name": "Flour", "quantity": "0E-1000000000"}],
        },
    )
    first = client.post("/api/v1/sync/push", json={"mutations": [body]})
    assert first.status_code == 200
    with app.state.database.connect() as db:
        stored = json.loads(
            db.execute("SELECT payload FROM entity WHERE id=?", (body["entity_id"],)).fetchone()[0]
        )
        assert stored["servings"] == "1.00"
        assert stored["ingredients"][0]["quantity"] == "0E-1000000000"
    assert client.post("/api/v1/sync/push", json={"mutations": [body]}).json() == first.json()
    unsafe = mutation(device, payload={"title": "Unsafe", "servings": "1e-1000000"})
    assert client.post("/api/v1/sync/push", json={"mutations": [unsafe]}).status_code == 422
    assert (
        client.post(
            "/api/v1/suggestions/weekly", params={"monday": "2026-10-19", "servings": "1e-1000000"}
        ).status_code
        == 422
    )
    with app.state.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM entity").fetchone()[0] == 1


def test_unsafe_legacy_quantity_fails_before_shopping_expansion(harness, mutation):
    client, app, device, _ = harness
    recipe = mutation(device)
    meal = mutation(
        device,
        kind="meal",
        payload={"recipe_id": recipe["entity_id"], "date": "2026-10-19", "category": "dinner"},
    )
    assert client.post("/api/v1/sync/push", json={"mutations": [recipe, meal]}).status_code == 200
    legacy = {
        "title": "Legacy",
        "servings": "2",
        "ingredients": [{"id": str(uuid4()), "name": "Flour", "quantity": "1e-1000000"}],
    }
    raw = json.dumps(legacy)
    with app.state.database.transaction() as db:
        db.execute("UPDATE entity SET payload=? WHERE id=?", (raw, recipe["entity_id"]))
    with app.state.database.connect() as db:
        with pytest.raises(ValidationError):
            shopping_projection(db, date(2026, 10, 19))
        assert (
            db.execute("SELECT payload FROM entity WHERE id=?", (recipe["entity_id"],)).fetchone()[
                0
            ]
            == raw
        )
