"""Explicitly creative AI suggestions, separate from factual recipe extraction."""

import hashlib
import json
import time
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from .ai_settings import load_configuration
from .auth import rate_limit
from .diagnostics import public_error
from .errors import DomainError
from .jobs import enqueue
from .models import Ingredient, Model, Recipe


class IdeaIngredient(Model):
    name: str = Field(min_length=1, max_length=200)
    quantity: Annotated[Decimal, Field(gt=0, le=1000000)] | None = None
    unit: str = Field(default="", max_length=30)
    preparation: str = Field(default="", max_length=300)
    original_text: str = Field(default="", max_length=500)


class RecipeIdea(Model):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    servings: Annotated[Decimal, Field(gt=0, le=1000)]
    ingredients: list[IdeaIngredient] = Field(min_length=1, max_length=40)
    steps: list[Annotated[str, Field(min_length=1, max_length=2000)]] = Field(
        min_length=1, max_length=30
    )


class GeneratedIdeas(Model):
    ideas: list[RecipeIdea] = Field(min_length=3, max_length=3)


class IdeaRequest(Model):
    request_id: UUID
    mode: Literal["ingredients", "surprise"]
    ingredients: str = Field(default="", max_length=2000)
    language: Literal["en", "de"] = "en"
    consent_external_ai: Literal[True]
    ai_destination: tuple[str, str, str]

    @model_validator(mode="after")
    def valid_input(self):
        if self.mode == "ingredients" and not self.ingredients:
            raise ValueError("Enter the ingredients you have")
        if self.mode == "surprise" and self.ingredients:
            raise ValueError("Surprise requests do not send ingredient text")
        return self


class IdeaStatus(Model):
    id: UUID
    state: Literal["queued", "running", "ready", "failed", "expired"]
    recipes: list[Recipe] = Field(default_factory=list)
    error_code: str | None = None


def status(database, iid):
    with database.connect() as db:
        row = db.execute("SELECT * FROM recipe_idea_request WHERE id=?", (str(iid),)).fetchone()
    if not row:
        raise DomainError("recipe_ideas_not_found", 404)
    return IdeaStatus(
        id=row["id"],
        state=row["state"],
        recipes=json.loads(row["recipes"] or "[]"),
        error_code=row["error_code"],
    )


def start(database, body):
    raw = body.model_dump_json()
    fingerprint = hashlib.sha256(raw.encode()).hexdigest()
    with database.transaction() as db:
        existing = db.execute(
            "SELECT fingerprint FROM recipe_idea_request WHERE id=?", (str(body.request_id),)
        ).fetchone()
        if existing:
            if existing[0] != fingerprint:
                raise DomainError("idempotency_conflict", 409)
        else:
            config = load_configuration(database.root / "config")
            check_configuration(config, body)
            if not rate_limit(db, "recipe.ideas", maximum=20, seconds=3600):
                raise DomainError("ai_request_limit", 429)
            now = time.time()
            db.execute(
                "INSERT INTO recipe_idea_request VALUES (?,?,?,'queued',NULL,NULL,?,?)",
                (str(body.request_id), fingerprint, raw, now, now),
            )
            enqueue(
                db, "recipe.ideas", "ideas:" + str(body.request_id), {"id": str(body.request_id)}
            )
    return status(database, body.request_id)


def check_configuration(config, body):
    if config is None or "text" not in config.formats:
        raise DomainError("ai_not_configured", 409)
    if tuple(body.ai_destination) != (config.provider, config.base_url, config.model):
        raise DomainError("ai_configuration_changed_review_consent", 409)
    if len(body.ingredients.encode()) > config.max_content:
        raise DomainError("ai_content_too_large", 422)


def process(database, payload, provider_factory):
    iid = str(payload["id"])
    with database.transaction() as db:
        row = db.execute("SELECT * FROM recipe_idea_request WHERE id=?", (iid,)).fetchone()
        if not row or row["state"] in ("ready", "failed", "expired"):
            return
        if row["state"] == "running":
            # A prior process might already have billed the provider. Never blindly
            # retry a non-idempotent generation after a crash/lost response.
            db.execute(
                "UPDATE recipe_idea_request SET state='failed',error_code='ai_generation_interrupted',updated_at=? WHERE id=?",
                (time.time(), iid),
            )
            return
        db.execute(
            "UPDATE recipe_idea_request SET state='running',updated_at=? WHERE id=?",
            (time.time(), iid),
        )
    try:
        body = IdeaRequest.model_validate_json(row["request"])
        config = load_configuration(database.root / "config")
        check_configuration(config, body)
        with database.transaction() as db:
            if not rate_limit(db, "ai.requests", maximum=config.requests_per_hour, seconds=3600):
                raise DomainError("ai_request_limit", 429)
        provider = provider_factory(config)
        try:
            generated = provider.generate_ideas(body.ingredients, body.language, body.mode)
        finally:
            provider.close()
        generated = GeneratedIdeas.model_validate(generated)
        recipes = [
            Recipe(
                title=idea.title,
                description=idea.description,
                servings=idea.servings,
                ingredients=[
                    Ingredient(id=uuid4(), **item.model_dump()) for item in idea.ingredients
                ],
                steps=idea.steps,
                source_platform="ai_generated",
                language=body.language,
                provenance={
                    "extractor": "ai-generated-ideas",
                    "provider": config.provider,
                    "model": config.model,
                    "review": "required",
                    "mode": body.mode,
                },
            ).model_dump(mode="json")
            for idea in generated.ideas
        ]
        with database.transaction() as db:
            db.execute(
                "UPDATE recipe_idea_request SET state='ready',recipes=?,updated_at=? WHERE id=? AND state='running'",
                (json.dumps(recipes), time.time(), iid),
            )
    except Exception as exc:
        code = public_error(exc.code) if isinstance(exc, DomainError) else "ai_generation_failed"
        with database.transaction() as db:
            db.execute(
                "UPDATE recipe_idea_request SET state='failed',error_code=?,updated_at=? WHERE id=? AND state='running'",
                (code, time.time(), iid),
            )
