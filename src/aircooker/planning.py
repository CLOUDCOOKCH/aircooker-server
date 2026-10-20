import hashlib
import json
import unicodedata
from datetime import date, timedelta
from decimal import Decimal

from .models import Meal, Recipe

UNITS = {
    "kg": ("g", Decimal(1000)),
    "g": ("g", Decimal(1)),
    "gram": ("g", Decimal(1)),
    "gramm": ("g", Decimal(1)),
    "l": ("ml", Decimal(1000)),
    "ml": ("ml", Decimal(1)),
    "liter": ("ml", Decimal(1000)),
    "litre": ("ml", Decimal(1000)),
    "tablespoon": ("tbsp", Decimal(1)),
    "el": ("tbsp", Decimal(1)),
    "teaspoon": ("tsp", Decimal(1)),
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
        if p["available"] and not p["include_this_week"]
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
            value = format(entry["quantity"].normalize(), "f")
            if entry["quantity_max"] is not None:
                value += "–" + format(entry["quantity_max"].normalize(), "f")
            entry["spec"] = f"{value} {entry['unit']}".strip()
        entry["sources"].sort()
    return requirements


def suggest(db, monday: date, seed: int = 0):
    recipes = entities(db, "recipe")
    meals = entities(db, "meal")
    occupied = set()
    last_cooked: dict[str, date] = {}
    used = set()
    for raw in meals.values():
        meal = Meal.model_validate(raw)
        for day in occurrences(meal, monday, monday + timedelta(days=6)):
            occupied.add((day, meal.category))
            used.add(str(meal.recipe_id))
        if meal.cooked and meal.date <= monday:
            rid = str(meal.recipe_id)
            last_cooked[rid] = max(last_cooked.get(rid, date.min), meal.date)
    results = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        if (day, "dinner") in occupied or not recipes:
            continue

        def score(pair):
            rid, recipe = pair
            recency = min(60, (monday - last_cooked.get(rid, monday - timedelta(days=60))).days)
            tie = int(hashlib.sha256(f"{seed}:{day}:{rid}".encode()).hexdigest()[:8], 16) % 10
            return (recipe.get("rating") or 3) * 5 + recency - (100 if rid in used else 0) + tie

        rid, recipe = max(recipes.items(), key=score)
        reasons = ["positively_rated" if (recipe.get("rating") or 0) >= 4 else "library_variety"]
        if rid not in last_cooked or (monday - last_cooked[rid]).days > 14:
            reasons.append("not_cooked_recently")
        results.append(
            {
                "recipe_id": rid,
                "date": str(day),
                "category": "dinner",
                "servings": recipe["servings"],
                "reasons": reasons,
            }
        )
        used.add(rid)
    return results
