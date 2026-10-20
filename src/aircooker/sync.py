import hashlib
import json
import time
from datetime import UTC, datetime

from .errors import DomainError
from .jobs import enqueue
from .models import ENTITY_MODELS, Change, Mutation, MutationResult, Pull
from .projections import project


def active(db, kind, entity_id):
    return db.execute(
        "SELECT * FROM entity WHERE kind=? AND id=? AND deleted=0", (kind, str(entity_id))
    ).fetchone()


def validate_references(db, kind, payload):
    if kind in ("meal", "leftover"):
        if not active(db, "recipe", payload["recipe_id"]):
            raise DomainError("recipe_not_found", 409)
    if kind == "template":
        for meal in payload["meals"]:
            if not active(db, "recipe", meal["recipe_id"]):
                raise DomainError("recipe_not_found", 409)
    if kind == "meal" and payload.get("leftover_id"):
        row = active(db, "leftover", payload["leftover_id"])
        if not row:
            raise DomainError("leftover_not_found", 409)
        leftover = json.loads(row["payload"])
        if leftover["discarded"] or leftover["recipe_id"] != payload["recipe_id"]:
            raise DomainError("invalid_leftover", 409)
        if payload["date"] < leftover["produced_on"]:
            raise DomainError("leftover_not_yet_produced", 409)
        from decimal import Decimal

        allocated = Decimal(0)
        for other in db.execute("SELECT payload FROM entity WHERE kind='meal' AND deleted=0"):
            meal = json.loads(other[0])
            if meal.get("leftover_id") == payload["leftover_id"]:
                allocated += Decimal(meal["servings"])
        return allocated
    return None


def apply_mutation(db, mutation: Mutation, device_id: str):
    if str(mutation.device_id) != device_id:
        raise DomainError("device_mismatch", 403)
    if mutation.idempotency_key != mutation.mutation_id:
        raise DomainError("idempotency_key_must_equal_mutation_id")
    raw = mutation.model_dump(mode="json")
    fingerprint = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()
    previous = db.execute(
        "SELECT * FROM mutation WHERE id=?", (str(mutation.mutation_id),)
    ).fetchone()
    if previous:
        if previous["device_id"] != device_id or previous["fingerprint"] != fingerprint:
            raise DomainError("idempotency_conflict", 409)
        return MutationResult.model_validate_json(previous["result"])
    kind, eid = mutation.kind, str(mutation.entity_id)
    existing = db.execute("SELECT * FROM entity WHERE kind=? AND id=?", (kind, eid)).fetchone()
    revision = existing["revision"] if existing else 0
    if mutation.base_revision > revision:
        raise DomainError("future_base_revision", 409)
    conflict = revision != mutation.base_revision
    if existing and existing["deleted"] and mutation.operation == "upsert":
        result = MutationResult(
            mutation_id=mutation.mutation_id,
            status="rejected_tombstone",
            revision=revision,
            conflict=True,
        )
    else:
        deleted = mutation.operation == "delete"
        payload = {}
        if not deleted:
            payload = (
                ENTITY_MODELS[kind]
                .model_validate(mutation.payload.model_dump() if mutation.payload else None)
                .model_dump(mode="json")
            )
            # Exclude this entity's former allocation while validating replacements.
            if kind == "meal" and existing:
                db.execute("UPDATE entity SET deleted=1 WHERE kind=? AND id=?", (kind, eid))
            allocated = validate_references(db, kind, payload)
            if allocated is not None:
                from decimal import Decimal

                leftover = json.loads(active(db, "leftover", payload["leftover_id"])["payload"])
                if allocated + Decimal(payload["servings"]) > Decimal(leftover["portions"]):
                    raise DomainError("insufficient_leftover_portions", 409)
        stamp = datetime.now(UTC).isoformat()
        encoded = json.dumps(payload, sort_keys=True)
        seq = db.execute(
            "INSERT INTO change_log(kind,entity_id,deleted,payload,updated_at) VALUES (?,?,?,?,?)",
            (kind, eid, deleted, encoded, stamp),
        ).lastrowid
        db.execute(
            "INSERT INTO entity VALUES (?,?,?,?,?,?) ON CONFLICT(kind,id) DO UPDATE SET revision=excluded.revision,deleted=excluded.deleted,payload=excluded.payload,updated_at=excluded.updated_at",
            (kind, eid, seq, deleted, encoded, stamp),
        )
        if kind == "recipe" and not deleted:
            provenance = payload.get("provenance", {})
            iid = provenance.get("import_job_id")
            if iid:
                draft = db.execute("SELECT * FROM import_draft WHERE id=?", (iid,)).fetchone()
                if (
                    not draft
                    or draft["state"] not in ("preview", "confirmed")
                    or provenance.get("reviewed_by_user") != "true"
                ):
                    raise DomainError("import_review_required", 409)
                if draft["confirmed_recipe_id"] and draft["confirmed_recipe_id"] != eid:
                    raise DomainError("import_already_confirmed", 409)
                db.execute(
                    "UPDATE import_draft SET state='confirmed',confirmed_recipe_id=? WHERE id=?",
                    (eid, iid),
                )
        project(db, kind, eid, payload, deleted)
        # Historical meals retain their references if a recipe is deleted. They
        # are displayed as unavailable and excluded from shopping projections.
        enqueue(db, "shopping.reconcile", "shopping.current", {})
        result = MutationResult(
            mutation_id=mutation.mutation_id,
            status="deleted" if deleted else "accepted",
            revision=seq,
            conflict=conflict,
        )
    db.execute(
        "INSERT INTO mutation VALUES (?,?,?,?,?)",
        (str(mutation.mutation_id), device_id, fingerprint, result.model_dump_json(), time.time()),
    )
    return result


def pull(db, cursor: int, limit: int):
    rows = list(
        db.execute(
            "SELECT * FROM change_log WHERE sequence>? ORDER BY sequence LIMIT ?",
            (cursor, limit + 1),
        )
    )
    changes = [
        Change(
            revision=r["sequence"],
            kind=r["kind"],
            entity_id=r["entity_id"],
            deleted=bool(r["deleted"]),
            payload=json.loads(r["payload"]),
            updated_at=r["updated_at"],
        )
        for r in rows[:limit]
    ]
    return Pull(
        changes=changes,
        cursor=changes[-1].revision if changes else cursor,
        has_more=len(rows) > limit,
    )
