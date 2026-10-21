"""Deterministic household-library recommendations. No AI or external calls."""

import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal

from .models import Meal
from .planning import entities, occurrences

CATEGORIES = ("breakfast", "lunch", "dinner")


def planning_basis(db):
    rows = [
        dict(row)
        for row in db.execute(
            "SELECT kind,id,revision,deleted,payload FROM entity WHERE kind IN ('recipe','meal','leftover') ORDER BY kind,id"
        )
    ]
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def tie(seed, day, category, rid):
    # Shared deterministic ordering with the native implementation; not a security hash.
    value = 14695981039346656037
    for byte in f"{seed}:{day}:{category}:{rid.lower()}".encode():
        value = ((value ^ byte) * 1099511628211) & ((1 << 64) - 1)
    return value % 10


def suggest_week(
    db,
    monday: date,
    seed=0,
    categories=("dinner",),
    allow_repeats=False,
    servings: Decimal | None = None,
):
    recipes = entities(db, "recipe")
    meals = [Meal.model_validate(raw) for raw in entities(db, "meal").values()]
    leftovers = entities(db, "leftover")
    occupied: set[tuple[date, str]] = set()
    used: dict[str, int] = {}
    last_cooked: dict[str, date] = {}
    last_planned: dict[str, date] = {}
    frequency: dict[str, int] = {}
    available = {lid: Decimal(raw["portions"]) for lid, raw in leftovers.items()}
    history_start = monday - timedelta(days=60)
    for meal in meals:
        rid = str(meal.recipe_id)
        if meal.leftover_id and str(meal.leftover_id) in available:
            available[str(meal.leftover_id)] -= meal.servings
        for day in occurrences(meal, monday, monday + timedelta(days=6)):
            occupied.add((day, meal.category))
            used[rid] = used.get(rid, 0) + 1
        for day in occurrences(meal, history_start, monday - timedelta(days=1)):
            last_planned[rid] = max(last_planned.get(rid, date.min), day)
            if day >= monday - timedelta(days=14):
                frequency[rid] = frequency.get(rid, 0) + 1
        # Cooked means explicitly marked, never inferred from a scheduled date.
        if meal.cooked and meal.date < monday:
            last_cooked[rid] = max(last_cooked.get(rid, date.min), meal.date)
    results = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        for category in (c for c in CATEGORIES if c in categories):
            if (day, category) in occupied:
                continue
            suitable = []
            for lid, raw in leftovers.items():
                recipe = recipes.get(raw["recipe_id"])
                if recipe is None or raw["discarded"] or raw["produced_on"] > str(day):
                    continue
                portions = servings if servings is not None else Decimal(recipe["servings"])
                if available[lid] >= portions:
                    suitable.append((raw["produced_on"], lid, raw, portions))
            if suitable:
                _, lid, raw, portions = min(suitable, key=lambda item: (item[0], item[1]))
                available[lid] -= portions
                rid = raw["recipe_id"]
                reasons = ["use_available_leftovers"]
            else:
                candidates = [
                    (rid, recipe)
                    for rid, recipe in recipes.items()
                    if allow_repeats or not used.get(rid)
                ]
                if not candidates:
                    continue

                def score(pair):
                    rid, recipe = pair
                    cooked_days = min(60, (monday - last_cooked.get(rid, history_start)).days)
                    planned_days = min(30, (monday - last_planned.get(rid, history_start)).days)
                    value = (
                        (recipe.get("rating") or 3) * 5
                        + cooked_days
                        + planned_days
                        - 10 * frequency.get(rid, 0)
                        + tie(seed, day, category, rid)
                    )
                    # Variety is a strict first priority; ratings/history break ties.
                    return (used.get(rid, 0), -value, rid)

                rid, recipe = min(candidates, key=score)
                lid = None
                portions = servings if servings is not None else Decimal(recipe["servings"])
                reasons = [
                    "positively_rated" if (recipe.get("rating") or 0) >= 4 else "library_variety"
                ]
                if rid not in last_cooked or (monday - last_cooked[rid]).days > 14:
                    reasons.append("not_cooked_recently")
                if not used.get(rid):
                    reasons.append("not_planned_this_week")
            results.append(
                dict(
                    recipe_id=rid,
                    date=str(day),
                    category=category,
                    servings=str(portions),
                    leftover_id=lid,
                    reasons=reasons,
                )
            )
            used[rid] = used.get(rid, 0) + 1
    return results
