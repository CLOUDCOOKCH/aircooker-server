"""Shared planning defaults and bounded, explicit-approval learning. No device-clock authority."""

import hashlib
import time
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends
from pydantic import Field, field_validator

from .auth import rate_limit
from .errors import DomainError
from .models import Model
from .quantities import PlanningServings

Category = Literal["breakfast", "lunch", "dinner"]


def default_categories() -> list[Category]:
    return ["dinner"]


class PlanningPreferences(Model):
    categories: list[Category] = Field(
        default_factory=default_categories, min_length=1, max_length=3
    )
    allow_repeats: bool = False
    servings: PlanningServings | None = None
    use_leftovers: bool = True

    @field_validator("categories")
    @classmethod
    def canonical_categories(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Choose each meal category once")
        return [category for category in ("breakfast", "lunch", "dinner") if category in value]


class PlanningContext(Model):
    revision: int = Field(ge=0)
    preferences: PlanningPreferences
    accepted_counts: dict[UUID, Annotated[int, Field(ge=1, le=1000000)]] = Field(max_length=10000)


class PreferenceWrite(Model):
    request_id: UUID
    base_revision: int = Field(ge=0)
    preferences: PlanningPreferences


class PreferenceReceipt(Model):
    request_id: UUID
    revision: int = Field(ge=1)
    conflict: bool


def context(db):
    row = db.execute("SELECT * FROM planning_preferences WHERE id=1").fetchone()
    return PlanningContext(
        revision=row["revision"],
        preferences=PlanningPreferences.model_validate_json(row["payload"]),
        accepted_counts={
            row["recipe_id"]: row["count"]
            for row in db.execute(
                "SELECT recipe_id,count FROM suggestion_acceptance ORDER BY recipe_id"
            )
        },
    )


def save_preferences(database, body, device_id):
    fingerprint = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
    with database.transaction() as db:
        prior = db.execute(
            "SELECT * FROM planning_preference_receipt WHERE id=?", (str(body.request_id),)
        ).fetchone()
        if prior:
            if prior["device_id"] != device_id or prior["fingerprint"] != fingerprint:
                raise DomainError("idempotency_conflict", 409)
            return PreferenceReceipt.model_validate_json(prior["result"])
        revision = db.execute("SELECT revision FROM planning_preferences WHERE id=1").fetchone()[0]
        receipt = PreferenceReceipt(
            request_id=body.request_id,
            revision=revision + 1,
            conflict=body.base_revision != revision,
        )
        db.execute(
            "UPDATE planning_preferences SET revision=?,payload=? WHERE id=1",
            (receipt.revision, body.preferences.model_dump_json()),
        )
        db.execute(
            "INSERT INTO planning_preference_receipt VALUES (?,?,?,?,?)",
            (str(body.request_id), device_id, fingerprint, receipt.model_dump_json(), time.time()),
        )
        return receipt


def register_routes(app, session, database):
    path = "/api/v1/household/planning-preferences"

    @app.get(path, response_model=PlanningContext)
    def get_preferences(current=Depends(session)):
        with database.connect() as db:
            db.execute("BEGIN")
            return context(db)

    @app.put(path, response_model=PreferenceReceipt)
    def put_preferences(body: PreferenceWrite, current=Depends(session)):
        with database.transaction() as db:
            allowed = rate_limit(db, "planning.preferences:" + current["device_id"], 120, 3600)
        if not allowed:
            raise DomainError("planning_preferences_request_limit", 429)
        return save_preferences(database, body, current["device_id"])
