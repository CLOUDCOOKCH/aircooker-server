"""Explicit data migrations run inside the same transaction as their schema migration.

Publish new canonical revisions; never rewrite immutable change history or replay receipts.
"""

import json
import time
from datetime import UTC, datetime
from uuid import UUID, uuid5
from zoneinfo import ZoneInfo

from .models import Mutation
from .planning import week_start
from .sync import apply_mutation


def pantry_periods(db):
    household = db.execute("SELECT instance_id,timezone FROM household WHERE id=1").fetchone()
    if not household:
        return
    rows = list(db.execute("SELECT * FROM entity WHERE kind='pantry' AND deleted=0"))
    candidates = [row for row in rows if json.loads(row["payload"]).get("include_this_week")]
    if not candidates:
        return
    device = str(uuid5(UUID(household["instance_id"]), "migration:006-pantry-period"))
    db.execute("INSERT OR IGNORE INTO device VALUES (?,?)", (device, time.time()))
    for row in candidates:
        payload = json.loads(row["payload"])
        if payload.get("include_week_start"):
            continue
        try:
            accepted = datetime.fromisoformat(row["updated_at"])
            if accepted.tzinfo is None:
                raise ValueError("No accepted timezone")
            day = accepted.astimezone(ZoneInfo(household["timezone"])).date()
            payload["include_week_start"] = week_start(day).isoformat()
        except (ValueError, OverflowError):
            # Unknown historical timing cannot safely authorise a new-period override.
            payload["include_this_week"] = False
            payload["include_week_start"] = None
        identity = str(uuid5(UUID(device), row["id"]))
        mutation = Mutation.model_validate(
            {
                "mutation_id": identity,
                "idempotency_key": identity,
                "entity_id": row["id"],
                "kind": "pantry",
                "operation": "upsert",
                "base_revision": row["revision"],
                "device_id": device,
                "client_timestamp": datetime.now(UTC).isoformat(),
                "payload": payload,
            }
        )
        apply_mutation(db, mutation, device, restoring=True)
    db.execute(
        "INSERT INTO audit_event(code,created_at) VALUES ('pantry_period_migration',?)",
        (time.time(),),
    )
