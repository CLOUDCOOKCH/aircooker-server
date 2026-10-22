"""Versioned non-secret exports; all database/media changes restore atomically."""

import base64
import binascii
import json
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import Field

from .errors import DomainError
from .legacy import ARCHIVE_FORMAT as LEGACY_ARCHIVE_FORMAT
from .media import MAX_IMAGE_BYTES, MediaInfo, info_for, insert_media, validate_archived_image
from .models import ENTITY_MODELS, EntityKind, HouseholdSettings, Model, Mutation
from .planning_preferences import PlanningPreferences, context
from .sync import apply_mutation

MAX_JSON_EXPORT = 8 * 1024 * 1024
MAX_MANIFEST = 8 * 1024 * 1024
MAX_ARCHIVE = 280 * 1024 * 1024


class ExportEntity(Model):
    kind: EntityKind
    id: UUID
    payload: dict
    deleted: bool = False


class ExportMedia(MediaInfo):
    data_base64: str = Field(max_length=4 * ((MAX_IMAGE_BYTES + 2) // 3))


class HouseholdExport(Model):
    format: str = "mealf-household"
    version: int = 3
    exported_at: str
    household: dict[str, str]
    entities: list[ExportEntity] = Field(max_length=10000)
    media: list[ExportMedia] = Field(default_factory=list, max_length=5000)
    planning_preferences: PlanningPreferences | None = None
    accepted_suggestions: dict[UUID, Annotated[int, Field(ge=1, le=1000000)]] = Field(
        default_factory=dict, max_length=10000
    )


class ArchiveManifest(Model):
    format: str = "mealf-household-archive"
    version: int = 1
    household: HouseholdExport
    media: list[MediaInfo] = Field(max_length=5000)


def snapshot(db):
    h = db.execute("SELECT name,timezone,language FROM household").fetchone()
    entities = []
    for row in db.execute("SELECT kind,id,payload,deleted FROM entity ORDER BY kind,id"):
        payload = json.loads(row["payload"])
        if row["deleted"] and not payload:
            # Older protocol tombstones retained the last snapshot only in the change log.
            prior = db.execute(
                "SELECT payload FROM change_log WHERE kind=? AND entity_id=? AND deleted=0 ORDER BY sequence DESC LIMIT 1",
                (row["kind"], row["id"]),
            ).fetchone()
            if prior:
                payload = json.loads(prior[0])
        entities.append(
            ExportEntity(
                kind=row["kind"], id=row["id"], payload=payload, deleted=bool(row["deleted"])
            )
        )
    planning = context(db)
    return HouseholdExport(
        exported_at=datetime.now(UTC).isoformat(),
        household=dict(h),
        entities=entities,
        planning_preferences=planning.preferences,
        accepted_suggestions=planning.accepted_counts,
    )


def referenced_media(body):
    return {
        str(UUID(entity.payload["image_id"]))
        for entity in body.entities
        if entity.kind == "recipe" and entity.payload.get("image_id")
    }


def export_household(database):
    with database.connect() as db:
        db.execute("BEGIN")
        body = snapshot(db)
        total = len(body.model_dump_json().encode())
        for image_id in sorted(referenced_media(body)):
            row = db.execute("SELECT * FROM recipe_media WHERE id=?", (image_id,)).fetchone()
            if not row:
                raise DomainError("export_image_missing", 409)
            total += 4 * ((row["byte_count"] + 2) // 3) + 1024
            if total > MAX_JSON_EXPORT:
                raise DomainError("export_too_large_use_archive", 413)
            body.media.append(
                ExportMedia(
                    **info_for(row).model_dump(), data_base64=base64.b64encode(row["data"]).decode()
                )
            )
        if total > MAX_JSON_EXPORT:
            raise DomainError("export_too_large_use_archive", 413)
        db.commit()
    return body


def apply_restore(db, body: HouseholdExport, device_id: str):
    from .legacy import EXPORT_FORMAT

    if body.format not in ("mealf-household", EXPORT_FORMAT) or body.version not in (1, 2, 3):
        raise DomainError("unsupported_export_format", 422)
    if body.version < 3 and (body.planning_preferences is not None or body.accepted_suggestions):
        raise DomainError("unsupported_export_fields", 422)
    settings = HouseholdSettings.model_validate(body.household)
    seen = set()
    order = {"recipe": 0, "pantry": 1, "leftover": 2, "template": 3, "meal": 4}
    ordered = sorted(body.entities, key=lambda e: order[e.kind])
    for entity in ordered:
        key = (entity.kind, str(entity.id))
        if key in seen or db.execute("SELECT 1 FROM entity WHERE kind=? AND id=?", key).fetchone():
            raise DomainError("duplicate_export_entity", 409)
        seen.add(key)
        if not entity.payload and entity.deleted:
            continue
        payload = ENTITY_MODELS[entity.kind].model_validate(entity.payload)
        mid = uuid4()
        apply_mutation(
            db,
            Mutation.model_validate(
                dict(
                    mutation_id=mid,
                    entity_id=entity.id,
                    kind=entity.kind,
                    operation="upsert",
                    base_revision=0,
                    payload=payload.model_dump(),
                    device_id=UUID(device_id),
                    client_timestamp=datetime.now(UTC),
                    idempotency_key=mid,
                )
            ),
            device_id,
            restoring=True,
        )
    # Restore reference targets before applying their tombstones, preserving meal history.
    for entity in ordered:
        if entity.deleted:
            row = db.execute(
                "SELECT revision FROM entity WHERE kind=? AND id=?", (entity.kind, str(entity.id))
            ).fetchone()
            mid = uuid4()
            apply_mutation(
                db,
                Mutation.model_validate(
                    dict(
                        mutation_id=mid,
                        entity_id=entity.id,
                        kind=entity.kind,
                        operation="delete",
                        base_revision=row[0] if row else 0,
                        payload=None,
                        device_id=UUID(device_id),
                        client_timestamp=datetime.now(UTC),
                        idempotency_key=mid,
                    )
                ),
                device_id,
                restoring=True,
            )
    db.execute(
        "UPDATE household SET name=?,timezone=?,language=? WHERE id=1",
        (settings.name, settings.timezone, settings.language),
    )
    if body.planning_preferences is not None:
        db.execute(
            "UPDATE planning_preferences SET revision=revision+1,payload=? WHERE id=1",
            (body.planning_preferences.model_dump_json(),),
        )
    imported_recipes = {
        entity.id for entity in body.entities if entity.kind == "recipe" and entity.payload
    }
    for recipe_id, count in body.accepted_suggestions.items():
        if recipe_id not in imported_recipes:
            raise DomainError("invalid_export_acceptance_recipe", 422)
        db.execute("INSERT INTO suggestion_acceptance VALUES (?,?)", (str(recipe_id), count))
    return {"imported": len(seen)}


def validate_export_media(body):
    assets = []
    seen = set()
    for asset in body.media:
        if asset.id in seen:
            raise DomainError("duplicate_export_media", 422)
        seen.add(asset.id)
        try:
            raw = base64.b64decode(asset.data_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise DomainError("invalid_export_media_encoding", 422) from exc
        validate_archived_image(raw, asset)
        assets.append((asset, raw))
    return assets


def import_household(database, body: HouseholdExport, device_id: str):
    assets = validate_export_media(body)
    with database.transaction() as db:
        for asset, raw in assets:
            insert_media(db, asset, raw)
        result = apply_restore(db, body, device_id)
    return {**result, "media_imported": len(assets)}


def export_archive(database) -> Path:
    fd = tempfile.NamedTemporaryFile(
        prefix=".export-", suffix=".zip", dir=database.root / "jobs", delete=False
    )
    target = Path(fd.name)
    fd.close()
    try:
        with (
            database.connect() as db,
            zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive,
        ):
            db.execute("BEGIN")
            body = snapshot(db)
            assets = []
            size = 0
            for image_id in sorted(referenced_media(body)):
                row = db.execute("SELECT * FROM recipe_media WHERE id=?", (image_id,)).fetchone()
                if not row:
                    raise DomainError("export_image_missing", 409)
                assets.append(info_for(row))
                size += row["byte_count"]
                if size > MAX_ARCHIVE - MAX_MANIFEST:
                    raise DomainError("export_archive_size_limit", 413)
                archive.writestr("media/" + image_id + ".jpg", row["data"])
            manifest = ArchiveManifest(household=body, media=assets).model_dump_json().encode()
            if len(manifest) > MAX_MANIFEST:
                raise DomainError("export_manifest_size_limit", 413)
            archive.writestr("manifest.json", manifest)
            db.commit()
        if target.stat().st_size > MAX_ARCHIVE:
            raise DomainError("export_archive_size_limit", 413)
        return target
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def import_archive(database, path: Path, device_id: str):
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)) or len(names) > 5001:
                raise DomainError("archive_duplicate_or_excess_entries", 422)
            if any(
                entry.flag_bits & 1
                or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                for entry in entries
            ):
                raise DomainError("archive_encoding_unsupported", 422)
            if sum(entry.file_size for entry in entries) > MAX_ARCHIVE:
                raise DomainError("archive_uncompressed_size_limit", 413)
            if (
                "manifest.json" not in names
                or archive.getinfo("manifest.json").file_size > MAX_MANIFEST
            ):
                raise DomainError("archive_manifest_invalid", 422)
            manifest = ArchiveManifest.model_validate_json(archive.read("manifest.json"))
            if (
                manifest.format not in ("mealf-household-archive", LEGACY_ARCHIVE_FORMAT)
                or manifest.version != 1
                or manifest.household.media
            ):
                raise DomainError("archive_format_unsupported", 422)
            ids = [str(asset.id) for asset in manifest.media]
            if len(ids) != len(set(ids)):
                raise DomainError("duplicate_export_media", 422)
            expected = {"manifest.json"} | {"media/" + image_id + ".jpg" for image_id in ids}
            if set(names) != expected:
                # Includes traversal, absolute paths, unexpected members and symlinks.
                raise DomainError("archive_unexpected_entries", 422)
            for asset in manifest.media:
                entry = archive.getinfo("media/" + str(asset.id) + ".jpg")
                if (
                    entry.file_size != asset.byte_count
                    or entry.file_size > MAX_IMAGE_BYTES
                    or (entry.external_attr >> 16) & 0o170000 == 0o120000
                ):
                    raise DomainError("archive_image_invalid", 422)
                validate_archived_image(archive.read(entry), asset)
            # The archive is never extracted to filesystem paths. A failed restore rolls back
            # media, entities, change cursors, tombstones, job enqueues and household settings.
            with database.transaction() as db:
                for asset in manifest.media:
                    insert_media(db, asset, archive.read("media/" + str(asset.id) + ".jpg"))
                result = apply_restore(db, manifest.household, device_id)
            return {**result, "media_imported": len(ids)}
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError) as exc:
        raise DomainError("archive_invalid", 422) from exc
