import hashlib
import json
import unicodedata
from datetime import date, timedelta
from decimal import Decimal

from .models import Meal, Recipe
from .quantities import fixed_amount

UNITS = {
    "kg": ("g", Decimal(1000)),
    "g": ("g", Decimal(1)),
    "gram": ("g", Decimal(1)),
    "grams": ("g", Decimal(1)),
    "gramm": ("g", Decimal(1)),
    "mg": ("g", Decimal("0.001")),
    "l": ("ml", Decimal(1000)),
    "ml": ("ml", Decimal(1)),
    "cl": ("ml", Decimal(10)),
    "dl": ("ml", Decimal(100)),
    "liter": ("ml", Decimal(1000)),
    "litre": ("ml", Decimal(1000)),
    "tablespoon": ("tbsp", Decimal(1)),
    "tablespoons": ("tbsp", Decimal(1)),
    "esslöffel": ("tbsp", Decimal(1)),
    "el": ("tbsp", Decimal(1)),
    "teaspoon": ("tsp", Decimal(1)),
    "teaspoons": ("tsp", Decimal(1)),
    "teelöffel": ("tsp", Decimal(1)),
    "tl": ("tsp", Decimal(1)),
    "piece": ("piece", Decimal(1)),
    "stück": ("piece", Decimal(1)),
}


def normalise(name: str):
    return " ".join(unicodedata.normalize("NFKC", name).casefold().split())


def week_start(day: date):
    return day - timedelta(days=day.weekday())


def occurrences(meal: Meal, start: date, end: date):
    if (end - start).days > 366 or end < start:
        raise ValueError("Calendar window must be between 0 and 366 days")
    if not meal.recurrence:
        return [meal.date] if start <= meal.date <= end else []
    rule = meal.recurrence
    step = 7 * rule.interval_weeks
    offset = max(0, ((start - meal.date).days + step - 1) // step)
    current = meal.date + timedelta(days=offset * step)
    result = []
    while current <= min(end, rule.until):
        if current not in rule.exceptions:
            result.append(current)
        current += timedelta(days=step)
    return result


def scaled(recipe: Recipe, servings: Decimal):
    ratio = servings / recipe.servings
    return [
        item.model_copy(
            update={
                "quantity": None if item.quantity is None else item.quantity * ratio,
                "quantity_max": None if item.quantity_max is None else item.quantity_max * ratio,
            }
        )
        for item in recipe.ingredients
    ]


def entities(db, kind):
    return {
        r["id"]: json.loads(r["payload"])
        for r in db.execute("SELECT * FROM entity WHERE kind=? AND deleted=0", (kind,))
    }


def shopping_projection(db, monday: date):
    recipes = entities(db, "recipe")
    pantry = {
        normalise(p["name"])
        for p in entities(db, "pantry").values()
        if p["available"]
        and not (p["include_this_week"] and p.get("include_week_start") == monday.isoformat())
    }
    requirements: dict[str, dict] = {}
    for mid, raw in entities(db, "meal").items():
        meal = Meal.model_validate(raw)
        if meal.leftover_id or str(meal.recipe_id) not in recipes:
            continue
        dates = occurrences(meal, monday, monday + timedelta(days=6))
        recipe = Recipe.model_validate(recipes[str(meal.recipe_id)])
        for day in dates:
            for item in scaled(recipe, meal.servings):
                name = normalise(item.name)
                if name in pantry:
                    continue
                unit, multiplier = UNITS.get(
                    normalise(item.unit), (normalise(item.unit), Decimal(1))
                )
                # Unquantified and range requirements remain separate, preserving text.
                opaque = item.quantity is None or item.quantity_max is not None
                key = f"{name}|{unit}" + (f"|{mid}|{day}|{item.id}" if opaque else "")
                rid = hashlib.sha256(key.encode()).hexdigest()
                quantity = None if item.quantity is None else item.quantity * multiplier
                entry = requirements.setdefault(
                    rid,
                    {
                        "id": rid,
                        "name": item.name,
                        "unit": unit,
                        "quantity": Decimal(0) if quantity is not None else None,
                        "quantity_max": None,
                        "original_text": item.original_text,
                        "sources": [],
                    },
                )
                if quantity is not None:
                    entry["quantity"] += quantity
                if item.quantity_max is not None:
                    entry["quantity_max"] = item.quantity_max * multiplier
                entry["sources"].append(f"{mid}:{day}:{item.id}:{meal.servings}")
    for entry in requirements.values():
        if entry["quantity"] is None:
            entry["spec"] = entry["original_text"] or "as needed"
        else:
            value = fixed_amount(entry["quantity"])
            if entry["quantity_max"] is not None:
                value += "–" + fixed_amount(entry["quantity_max"])
            entry["spec"] = f"{value} {entry['unit']}".strip()
        entry["sources"].sort()
    return requirements


def suggest(db, monday: date, seed: int = 0):
    from .recommendations import suggest_week

    return suggest_week(db, monday, seed)
