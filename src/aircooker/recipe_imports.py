"""Recipe import orchestration: metadata first, optional AI, then explicit human review."""

import json
import time
from uuid import uuid4

from pydantic import ValidationError

from .ai import AIInput
from .ai_settings import load_configuration
from .auth import rate_limit
from .errors import DomainError
from .import_sources import youtube_url


def process_import(database, payload, *, fetch, provider_factory, extractor):
    iid = payload["id"]
    with database.connect() as db:
        draft = db.execute("SELECT * FROM import_draft WHERE id=?", (iid,)).fetchone()
    if not draft or draft["state"] in ("cancelled", "confirmed"):
        return
    attempt = None
    extraction = None
    recipe = None
    try:
        source = None
        if draft["source_id"]:
            with database.connect() as db:
                source = db.execute(
                    "SELECT * FROM import_source WHERE id=?", (draft["source_id"],)
                ).fetchone()
            if source is None:
                raise DomainError("import_source_expired", 410)
            content = payload.get("text") or ""
        else:
            content = payload.get("text") or fetch(draft["source_url"])
        if source is None:
            try:
                recipe, warnings = extractor(content, draft["source_url"], draft["source_platform"])
                if not recipe.ingredients or not recipe.steps:
                    raise DomainError("structured_recipe_incomplete", 422)
            except (DomainError, ValidationError, ValueError, TypeError, RecursionError):
                if not payload.get("use_ai"):
                    raise DomainError("structured_recipe_not_found_use_manual_entry", 422)
                recipe = None
        if recipe is None:
            config = load_configuration(database.root / "config")
            if config is None:
                raise DomainError("ai_not_configured", 409)
            if not payload.get("consent_external_ai"):
                raise DomainError("ai_content_disclosure_consent_required", 422)
            if payload.get("ai_destination") not in (
                None,
                [config.provider, config.base_url, config.model],
            ):
                raise DomainError("ai_configuration_changed_review_consent", 409)
            video = None
            if source is None and draft["source_platform"] == "youtube" and not payload.get("text"):
                video = youtube_url(draft["source_url"])
                content = "Extract the recipe visible or spoken in this public cooking video."
            value = AIInput(
                text=content,
                data=source["data"] if source else b"",
                media_type=source["content_type"] if source else "",
                video_url=video,
            )
            if value.kind not in config.formats:
                raise DomainError("ai_input_format_unsupported", 422)
            if len(value.text.encode()) > config.max_content:
                raise DomainError("ai_content_too_large", 422)
            with database.transaction() as db:
                if not rate_limit(
                    db, "ai.requests", maximum=config.requests_per_hour, seconds=3600
                ):
                    raise DomainError("ai_request_limit", 429)
                attempt = str(uuid4())
                db.execute(
                    "INSERT INTO import_ai_attempt VALUES (?,?,?,?,?,'started',NULL,?)",
                    (attempt, iid, config.provider, config.model, value.kind, time.time()),
                )
            provider = provider_factory(config)
            try:
                extraction = provider.extract(value)
            finally:
                provider.close()
            recipe = extraction.reviewed_preview()
            if recipe:
                recipe.source_url = draft["source_url"]
                recipe.source_platform = draft["source_platform"]
            warnings = ["ai_extracted_review_all_fields"]
            if value.kind in {"video", "youtube"}:
                warnings.append("video_first_ten_minutes")
            if extraction.recipe.servings is None:
                warnings.append("review_servings")
        with database.transaction() as db:
            db.execute(
                "UPDATE import_draft SET state='preview',recipe=?,extraction=?,warnings=?,error_code=NULL WHERE id=? AND state NOT IN ('cancelled','confirmed')",
                (
                    recipe.model_dump_json() if recipe else None,
                    extraction.model_dump_json(by_alias=True) if extraction else None,
                    json.dumps(warnings),
                    iid,
                ),
            )
            if attempt:
                db.execute("UPDATE import_ai_attempt SET state='succeeded' WHERE id=?", (attempt,))
    except (DomainError, ValidationError) as exc:
        code = exc.code if isinstance(exc, DomainError) else "invalid_extracted_recipe"
        with database.transaction() as db:
            db.execute(
                "UPDATE import_draft SET state='needs_input',error_code=? WHERE id=? AND state NOT IN ('cancelled','confirmed')",
                (code, iid),
            )
            if attempt:
                db.execute(
                    "UPDATE import_ai_attempt SET state='failed',error_code=? WHERE id=?",
                    (code, attempt),
                )
