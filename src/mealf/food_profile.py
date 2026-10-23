"""Household food choices, separate from entity sync and planning defaults."""

import hashlib
import json
import time
import unicodedata
from importlib.resources import files
from uuid import UUID

from fastapi import Depends
from pydantic import Field, ValidationError, field_validator, model_validator

from .auth import rate_limit
from .errors import DomainError
from .models import Model

CATALOG = json.loads(files("mealf").joinpath("food_catalog.json").read_text())
TASTES = {item["id"]: item for item in CATALOG["items"] if item["taste"]}


def name_key(name):
    return " ".join(unicodedata.normalize("NFKC", name).casefold().split())


PANTRY_ALIASES = {
    name_key(alias): item["id"]
    for item in CATALOG["items"]
    if item["pantry_group"]
    for alias in item["aliases"] + list(item["name"].values())
}


def pantry_key(name):
    # Only curated exact translations, never fuzzy ingredient or Bring ownership matching.
    key = name_key(name)
    return "catalog:" + PANTRY_ALIASES[key] if key in PANTRY_ALIASES else "name:" + key


class FoodTaste(Model):
    likes: list[str] = Field(default_factory=list, max_length=12)
    dislikes: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("likes", "dislikes")
    @classmethod
    def known_choices(cls, value):
        if len(set(value)) != len(value) or any(item not in TASTES for item in value):
            raise ValueError("Choose known foods once")
        return sorted(value)

    @model_validator(mode="after")
    def separate_choices(self):
        if set(self.likes) & set(self.dislikes):
            raise ValueError("A food cannot be both liked and disliked")
        return self

    def prompt_data(self):
        return {
            "liked_foods": [TASTES[item]["name"]["en"] for item in self.likes],
            "disliked_foods": [TASTES[item]["name"]["en"] for item in self.dislikes],
        }


class FoodProfile(FoodTaste):
    pantry_setup_done: bool = False
    taste_setup_done: bool = False


class FoodProfilePatch(Model):
    likes: list[str] | None = Field(default=None, max_length=12)
    dislikes: list[str] | None = Field(default=None, max_length=12)
    pantry_setup_done: bool | None = None
    taste_setup_done: bool | None = None

    @model_validator(mode="after")
    def explicit_fields(self):
        if not self.model_fields_set or any(
            getattr(self, key) is None for key in self.model_fields_set
        ):
            raise ValueError("Provide a non-null food preference change")
        for key in ("likes", "dislikes"):
            if key in self.model_fields_set:
                setattr(self, key, FoodTaste.known_choices(getattr(self, key)))
        return self


class FoodProfileContext(Model):
    revision: int = Field(ge=0)
    profile: FoodProfile


class FoodProfileWrite(Model):
    request_id: UUID
    base_revision: int = Field(ge=0)
    patch: FoodProfilePatch


class FoodProfileReceipt(Model):
    request_id: UUID
    revision: int = Field(ge=1)
    conflict: bool


def context(db):
    row = db.execute("SELECT * FROM food_profile WHERE id=1").fetchone()
    return FoodProfileContext(
        revision=row["revision"], profile=FoodProfile.model_validate_json(row["payload"])
    )


def save(database, body, device_id):
    raw = body.model_dump_json(exclude_none=True)
    fingerprint = hashlib.sha256(raw.encode()).hexdigest()
    with database.transaction() as db:
        prior = db.execute(
            "SELECT * FROM food_profile_receipt WHERE id=?", (str(body.request_id),)
        ).fetchone()
        if prior:
            if prior["device_id"] != device_id or prior["fingerprint"] != fingerprint:
                raise DomainError("idempotency_conflict", 409)
            return FoodProfileReceipt.model_validate_json(prior["result"])
        current = context(db)
        try:
            merged = FoodProfile.model_validate(
                {**current.profile.model_dump(), **body.patch.model_dump(exclude_none=True)}
            )
        except ValidationError as exc:
            raise DomainError("invalid_food_preferences", 422) from exc
        receipt = FoodProfileReceipt(
            request_id=body.request_id,
            revision=current.revision + 1,
            conflict=body.base_revision != current.revision,
        )
        db.execute(
            "UPDATE food_profile SET revision=?,payload=? WHERE id=1",
            (receipt.revision, merged.model_dump_json()),
        )
        db.execute(
            "INSERT INTO food_profile_receipt VALUES (?,?,?,?,?)",
            (str(body.request_id), device_id, fingerprint, receipt.model_dump_json(), time.time()),
        )
        return receipt


def register_routes(app, session, database):
    path = "/api/v1/household/food-profile"

    @app.get(path, response_model=FoodProfileContext)
    def get_profile(current=Depends(session)):
        with database.connect() as db:
            return context(db)

    @app.put(path, response_model=FoodProfileReceipt)
    def put_profile(body: FoodProfileWrite, current=Depends(session)):
        with database.transaction() as db:
            allowed = rate_limit(db, "food.profile:" + current["device_id"], 120, 3600)
        if not allowed:
            raise DomainError("food_preferences_request_limit", 429)
        return save(database, body, current["device_id"])
