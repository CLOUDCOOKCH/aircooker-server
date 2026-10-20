import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import Field

from .errors import DomainError
from .models import ENTITY_MODELS, EntityKind, HouseholdSettings, Model, Mutation
from .sync import apply_mutation


class ExportEntity(Model):
    kind: EntityKind
    id: UUID
    payload: dict


class HouseholdExport(Model):
    format: str = "aircooker-household"
    version: int = 1
    exported_at: str
    household: dict[str, str]
    entities: list[ExportEntity] = Field(max_length=10000)


def export_household(database):
    with database.connect() as db:
        db.execute("BEGIN")
        h = db.execute("SELECT name,timezone,language FROM household").fetchone()
        rows = list(
            db.execute("SELECT kind,id,payload FROM entity WHERE deleted=0 ORDER BY kind,id")
        )
        result = HouseholdExport(
            exported_at=datetime.now(UTC).isoformat(),
            household=dict(h),
            entities=[
                ExportEntity(kind=r["kind"], id=r["id"], payload=json.loads(r["payload"]))
                for r in rows
            ],
        )
        db.commit()
    return result


def import_household(database, body: HouseholdExport, device_id: str):
    if body.format != "aircooker-household" or body.version != 1:
        raise DomainError("unsupported_export_format", 422)
    order = {"recipe": 0, "pantry": 1, "leftover": 2, "template": 3, "meal": 4}
    seen = set()
    with database.transaction() as db:
        for entity in sorted(body.entities, key=lambda e: order[e.kind]):
            key = (entity.kind, str(entity.id))
            if (
                key in seen
                or db.execute("SELECT 1 FROM entity WHERE kind=? AND id=?", key).fetchone()
            ):
                raise DomainError("duplicate_export_entity", 409)
            seen.add(key)
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
            )
        settings = HouseholdSettings.model_validate(body.household)
        db.execute(
            "UPDATE household SET name=?,timezone=?,language=? WHERE id=1",
            (settings.name, settings.timezone, settings.language),
        )
    return {"imported": len(seen)}
