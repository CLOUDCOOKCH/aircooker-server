"""Transactional live-preview approval and durable request replay receipts."""

import hashlib
import json
import time
from datetime import date, timedelta

from .errors import DomainError
from .models import Meal
from .planning import entities, occurrences, week_start
from .recommendations import planning_basis
from .sync import apply_mutation


def apply_preview(database, body, device_id):
    fingerprint = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
    with database.transaction() as db:
        prior = db.execute(
            "SELECT * FROM suggestion_application WHERE id=?", (str(body.request_id),)
        ).fetchone()
        if prior:
            if prior["device_id"] != device_id or prior["fingerprint"] != fingerprint:
                raise DomainError("idempotency_conflict", 409)
            return json.loads(prior["result"])
        if body.monday != week_start(body.monday):
            raise DomainError("week_must_start_monday", 422)
        if planning_basis(db) != body.basis:
            raise DomainError("suggestion_preview_stale", 409)
        end = body.monday + timedelta(days=6)
        occupied: set[tuple[date, str]] = set()
        for raw in entities(db, "meal").values():
            meal = Meal.model_validate(raw)
            occupied.update((day, meal.category) for day in occurrences(meal, body.monday, end))
        results = []
        for mutation in body.mutations:
            if (
                mutation.kind != "meal"
                or mutation.operation != "upsert"
                or mutation.base_revision != 0
                or db.execute(
                    "SELECT 1 FROM entity WHERE kind='meal' AND id=?", (str(mutation.entity_id),)
                ).fetchone()
            ):
                raise DomainError("suggestions_must_add_new_meals", 422)
            meal = Meal.model_validate(mutation.payload.model_dump() if mutation.payload else None)
            if meal.recurrence or meal.cooked or not body.monday <= meal.date <= end:
                raise DomainError("invalid_suggested_meal", 422)
            if (meal.date, meal.category) in occupied:
                raise DomainError("suggestion_slot_occupied", 409)
            occupied.add((meal.date, meal.category))
            results.append(apply_mutation(db, mutation, device_id).model_dump(mode="json"))
        db.execute(
            "INSERT INTO suggestion_application VALUES (?,?,?,?,?)",
            (str(body.request_id), device_id, fingerprint, json.dumps(results), time.time()),
        )
        return results
