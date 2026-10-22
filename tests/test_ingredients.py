import json
from decimal import Decimal
from uuid import uuid4

import pytest

from mealf.ingredients import parse_ingredient
from mealf.models import Recipe
from mealf.planning import scaled


@pytest.mark.parametrize(
    "source,name,quantity,unit,maximum,preparation",
    [
        ("200 g flour", "flour", "200", "g", None, ""),
        ("500ml milk", "milk", "500", "ml", None, ""),
        ("2 onions", "onions", "2", "", None, ""),
        ("1 tablespoon olive oil", "olive oil", "1", "tbsp", None, ""),
        ("1/2 tsp salt", "salt", "0.5", "tsp", None, ""),
        ("1 1/2 cups flour", "flour", "1.5", "cup", None, ""),
        ("1½ EL Olivenöl", "Olivenöl", "1.5", "tbsp", None, ""),
        ("1,5 kg Kartoffeln", "Kartoffeln", "1.5", "kg", None, ""),
        ("0,125 l Milch", "Milch", "0.125", "l", None, ""),
        ("½–¾ TL Salz", "Salz", "0.5", "tsp", "0.75", ""),
        ("200 - 250 g Möhren, fein gewürfelt", "Möhren", "200", "g", "250", "fein gewürfelt"),
        ("2 Stück Zwiebeln", "Zwiebeln", "2", "piece", None, ""),
    ],
)
def test_supported_quantities_keep_source_text(source, name, quantity, unit, maximum, preparation):
    ingredient = parse_ingredient(source)
    assert ingredient.original_text == source
    assert ingredient.name == name
    assert ingredient.quantity == Decimal(quantity)
    assert ingredient.quantity_max == (Decimal(maximum) if maximum else None)
    assert ingredient.unit == unit and ingredient.preparation == preparation


@pytest.mark.parametrize(
    "source",
    [
        "1,000 g flour",
        "1.000 g Mehl",
        "1/0 tsp salt",
        "3–2 onions",
        "-2 onions",
        "2 (400 g) cans tomatoes",
        "2 x 400 g tomatoes",
        "2 x400g tomatoes",
        "1 heaped tsp salt",
        "1e3 g flour",
        "1000001 g flour",
        "1.2.3 g flour",
        "flour as much as you prefer",
    ],
)
def test_ambiguous_and_unsupported_quantities_stay_unparsed(source):
    ingredient = parse_ingredient(source)
    assert ingredient.quantity is None and ingredient.quantity_max is None
    assert ingredient.name == source and ingredient.original_text == source


@pytest.mark.parametrize(
    "source,name,note",
    [
        ("salt to taste", "salt", "to taste"),
        ("Salz nach Geschmack", "Salz", "nach Geschmack"),
        ("water as needed", "water", "as needed"),
    ],
)
def test_non_numeric_ingredients_remain_sensible_when_scaling(source, name, note):
    ingredient = parse_ingredient(source)
    recipe = Recipe(title="Soup", ingredients=[ingredient])
    result = scaled(recipe, Decimal(8))[0]
    assert result.name == name and result.preparation == note
    assert result.quantity is None and result.original_text == source


def test_import_reviewed_fraction_flows_into_scaled_shopping_projection(harness, mutation):
    from datetime import date

    from mealf.jobs import claim, finish
    from mealf.planning import shopping_projection

    client, app, device, _ = harness
    source = json.dumps(
        {
            "@type": "Recipe",
            "name": "Bread",
            "recipeYield": "2",
            "recipeIngredient": [
                "½ kg flour",
                "250 g flour",
                "1 dl milk",
                "100 ml milk",
                "salt to taste",
            ],
            "recipeInstructions": ["Mix"],
        }
    )
    response = client.post("/api/v1/imports", json={"text": source})
    job = claim(app.state.database)
    app.state.process_job(job)
    finish(app.state.database, job)
    draft = client.get("/api/v1/imports/" + response.json()["id"]).json()
    assert draft["state"] == "preview"
    assert client.get("/api/v1/recipes").json()["items"] == []
    recipe_id = str(uuid4())
    saved = mutation(device, entity_id=recipe_id, payload=draft["recipe"])
    assert client.post("/api/v1/imports/" + draft["id"] + "/confirm", json=saved).status_code == 200
    meal = mutation(
        device,
        kind="meal",
        payload={
            "recipe_id": recipe_id,
            "date": "2026-10-19",
            "category": "dinner",
            "servings": "4",
        },
    )
    assert client.post("/api/v1/calendar/meals", json=meal).status_code == 201
    with app.state.database.connect() as db:
        required = {
            row["name"]: row for row in shopping_projection(db, date(2026, 10, 19)).values()
        }
    assert required["flour"]["quantity"] == 1500 and required["flour"]["unit"] == "g"
    assert required["milk"]["quantity"] == 400 and required["milk"]["unit"] == "ml"
    assert required["salt"]["quantity"] is None
    pantry = mutation(device, kind="pantry", payload={"name": "salt", "available": True})
    assert client.post("/api/v1/pantry", json=pantry).status_code == 201
    with app.state.database.connect() as db:
        required = list(shopping_projection(db, date(2026, 10, 19)).values())
    assert {row["name"] for row in required} == {"flour", "milk"}


@pytest.mark.parametrize("raw", ["200 g flour", [None, "", "200 g flour"]])
def test_unsupported_ingredient_entries_are_disclosed(raw):
    from mealf.importing import extract

    recipe, warnings = extract(
        json.dumps(
            {
                "@type": "Recipe",
                "name": "Bread",
                "recipeIngredient": raw,
            }
        )
    )
    assert "ingredient_entries_omitted" in warnings
    assert all(ingredient.name for ingredient in recipe.ingredients)


def test_import_limits_disclose_truncated_source_text():
    from mealf.importing import extract

    recipe, warnings = extract(
        json.dumps(
            {
                "@type": "Recipe",
                "name": "Bread",
                "recipeIngredient": ["a" * 501],
            }
        )
    )
    assert "ingredient_text_truncated" in warnings
    assert len(recipe.ingredients[0].original_text) == 500
