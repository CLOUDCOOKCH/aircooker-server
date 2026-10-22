"""Recipe import orchestration: metadata first, optional AI, then explicit human review."""

import hashlib
import json
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4, uuid5

from pydantic import ValidationError

from .ai import AIInput
from .ai_settings import load_configuration
from .auth import rate_limit
from .errors import DomainError
from .image_import import printed_recipe
from .import_sources import youtube_url
from .importing import FetchedPage
from .media import MediaInfo, insert_media


def process_import(
    database,
    payload,
    *,
    fetch,
    provider_factory,
    extractor,
    recognise,
    personal_extract=None,
    source_photo=None,
):
    iid = payload["id"]
    with database.connect() as db:
        draft = db.execute("SELECT * FROM import_draft WHERE id=?", (iid,)).fetchone()
    if not draft or draft["state"] in ("cancelled", "confirmed"):
        return
    with database.connect() as db:
        saved_photo = db.execute(
            "SELECT m.data,m.width,m.height,p.source_url FROM import_source_photo p "
            "JOIN recipe_media m ON m.id=p.image_id WHERE p.import_id=?",
            (iid,),
        ).fetchone()
    attempt = None
    extraction = None
    recipe = None
    try:
        source = None
        page = None
        image_id = payload.get("image_id")
        if image_id:
            content = payload.get("text")
            if not content:
                with database.connect() as db:
                    media = db.execute(
                        "SELECT data FROM recipe_media WHERE id=?", (image_id,)
                    ).fetchone()
                if not media:
                    raise DomainError("image_not_found", 404)
                content = recognise(media["data"])
            with database.transaction() as db:
                updated = db.execute(
                    "UPDATE import_draft SET recognized_text=? WHERE id=? AND state NOT IN ('cancelled','confirmed')",
                    (content, iid),
                ).rowcount
            if not updated:
                return
            if not payload.get("use_ai"):
                recipe, warnings = printed_recipe(content, image_id, draft["source_url"])
        elif draft["source_id"]:
            with database.connect() as db:
                source = db.execute(
                    "SELECT * FROM import_source WHERE id=?", (draft["source_id"],)
                ).fetchone()
            if source is None:
                raise DomainError("import_source_expired", 410)
            content = payload.get("text") or ""
        else:
            content = payload.get("text")
            if not content:
                fetched = fetch(draft["source_url"])
                if isinstance(fetched, FetchedPage):
                    page, content = fetched, fetched.text
                else:
                    content = fetched
        if source is None and not image_id:
            try:
                recipe, warnings = extractor(content, draft["source_url"], draft["source_platform"])
                if not recipe.ingredients or not recipe.steps:
                    raise DomainError("structured_recipe_incomplete", 422)
            except (DomainError, ValidationError, ValueError, TypeError, RecursionError):
                if not payload.get("use_ai"):
                    raise DomainError("structured_recipe_not_found_use_manual_entry", 422)
                recipe = None
        if recipe is None and payload.get("ai_account") == "chatgpt":
            with database.connect() as db:
                owner = db.execute(
                    "SELECT * FROM chatgpt_import WHERE import_id=?", (iid,)
                ).fetchone()
            if (
                not owner
                or personal_extract is None
                or not payload.get("consent_chatgpt_background")
                or not payload.get("consent_external_ai")
            ):
                raise DomainError("chatgpt_plan_permission_required", 409)
            destination = payload.get("ai_destination")
            if not destination or destination[:2] != ["chatgpt", "https://api.openai.com/v1"]:
                raise DomainError("chatgpt_configuration_changed", 409)
            extraction = personal_extract(
                owner["session_id"], owner["connection_id"], destination[2], content
            )
            recipe = extraction.reviewed_preview()
            if recipe:
                recipe.source_platform = "supplied_text"
                recipe.provenance["extractor"] = "chatgpt-personal-plan"
            warnings = ["ai_extracted_review_all_fields"]
            if extraction.recipe.servings is None:
                warnings.append("review_servings")
        elif recipe is None:
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
                if image_id:
                    # Existing camera imports retain their text-only privacy contract.
                    recipe = provider.extract_recipe(content)
                else:
                    extraction = provider.extract(value)
            finally:
                provider.close()
            if extraction:
                recipe = extraction.reviewed_preview()
            if recipe:
                recipe.source_url = draft["source_url"]
                recipe.source_platform = draft["source_platform"]
            warnings = ["ai_extracted_review_all_fields"]
            if value.kind in {"video", "youtube"}:
                warnings.append("video_first_ten_minutes")
            if extraction and extraction.recipe.servings is None:
                warnings.append("review_servings")
            if image_id and recipe is not None:
                recipe.image_id = UUID(image_id)
                recipe.provenance["input"] = (
                    "local-image-ocr" if not payload.get("text") else "user_corrected_image_text"
                )
                warnings.append("image_text_requires_review")
        photo = tuple(saved_photo) if saved_photo else None
        if not photo and (
            (recipe or extraction)
            and not (recipe and recipe.image_id)
            and draft["source_url"]
            and source_photo
        ):
            try:
                photo = source_photo(draft["source_url"], page)
            except (DomainError, OSError, ValueError):
                pass
            if not photo:
                warnings.append("source_image_unavailable")
        with database.transaction() as db:
            active = db.execute("SELECT state FROM import_draft WHERE id=?", (iid,)).fetchone()
            if not active or active["state"] in ("cancelled", "confirmed"):
                if attempt:
                    db.execute(
                        "UPDATE import_ai_attempt SET state='succeeded' WHERE id=?", (attempt,)
                    )
                return
            if photo:
                data, width, height, origin = photo
                info = MediaInfo(
                    id=uuid5(UUID(iid), "source-photo"),
                    sha256=hashlib.sha256(data).hexdigest(),
                    byte_count=len(data),
                    width=width,
                    height=height,
                    created_at=datetime.now(UTC).isoformat(),
                )
                try:
                    insert_media(db, info, data)
                    db.execute(
                        "INSERT INTO import_source_photo VALUES (?,?,?) ON CONFLICT(import_id) DO NOTHING",
                        (iid, str(info.id), origin),
                    )
                    if recipe:
                        recipe.image_id = info.id
                        recipe.provenance["image_source"] = origin
                        recipe.provenance["image_extractor"] = "source-metadata-v1"
                except DomainError:
                    warnings.append("source_image_unavailable")
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
