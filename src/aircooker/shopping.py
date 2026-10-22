"""Read-only weekly requirements and observable durable Bring reconciliation."""

import hashlib
import json
import time
from datetime import date, datetime
from typing import Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from .auth import rate_limit
from .diagnostics import public_error
from .errors import DomainError
from .jobs import enqueue
from .models import Meal, Model
from .planning import entities, normalise, occurrences, shopping_projection, week_start
from .secrets import SecretVault

ShoppingItemState = Literal[
    "not_sent", "pending", "synced", "purchased", "removed_by_user", "manual"
]


class ShoppingItem(Model):
    id: str
    name: str
    spec: str
    sources: int
    state: Literal["not_sent", "pending", "synced", "purchased", "removed_by_user", "manual"]


class ShoppingSnapshot(Model):
    period: date
    calculated_at: float
    planned_meals: int
    excluded_staples: list[str]
    requirements: list[ShoppingItem]
    last_success_at: float | None
    job_state: Literal["idle", "queued", "running", "done", "failed"]
    error_code: str | None
    verification_state: Literal["idle", "queued", "running", "done", "failed"]
    verification_error: str | None
    list_id: str | None
    list_name: str | None
    connection_state: Literal[
        "not_configured", "list_not_selected", "compatibility_unverified", "ready"
    ]


class BringVerification(Model):
    list_id: UUID
    dedicated_test_list_confirmed: Literal[True]


def configuration_hash(raw):
    # Bind capability evidence to this exact credential/list configuration; never expose it.
    return hashlib.sha256(raw.encode()).hexdigest()


def settings(database):
    return SecretVault(database.root / "config").load("bring")


def snapshot(database, capability_factory):
    raw = settings(database)
    config = json.loads(raw) if raw else {}
    list_id = config.get("list_id")
    ready = False
    if raw and list_id:
        connector = capability_factory(database.root / "config")
        try:
            c = connector.capabilities
            ready = all((c.uuid_create, c.uuid_update, c.uuid_remove, c.completed_status))
        finally:
            connector.runner.close()
    with database.connect() as db:
        db.execute("BEGIN")  # One coherent recipe/meal/ledger/job read snapshot.
        household = db.execute("SELECT timezone FROM household").fetchone()
        monday = week_start(datetime.now(ZoneInfo(household[0])).date())
        desired = shopping_projection(db, monday)
        meal_count = sum(
            len(
                occurrences(
                    Meal.model_validate(m), monday, date.fromordinal(monday.toordinal() + 6)
                )
            )
            for m in entities(db, "meal").values()
        )
        excluded = sorted(
            {
                p["name"]
                for p in entities(db, "pantry").values()
                if p["available"]
                and not (p["include_this_week"] and p.get("include_week_start") == str(monday))
            }
        )
        ledger = {
            r["requirement_id"]: dict(r)
            for r in db.execute(
                "SELECT * FROM bring_owned_item WHERE period=? AND list_id=?",
                (str(monday), list_id),
            )
        }
        success = db.execute("SELECT * FROM shopping_sync WHERE slot=1").fetchone()
        manual = set()
        success_at = None
        if success and success["period"] == str(monday) and success["list_id"] == list_id:
            manual = set(json.loads(success["manual_names"]))
            success_at = success["completed_at"]
        jobs = {
            r["dedupe_key"]: dict(r)
            for r in db.execute(
                "SELECT * FROM background_job WHERE dedupe_key IN ('shopping.current','bring.verify')"
            )
        }
    items = []
    for rid, item in desired.items():
        owned = ledger.get(rid)
        state: ShoppingItemState = "manual" if normalise(item["name"]) in manual else "not_sent"
        if owned:
            if owned["state"] in ("purchased", "removed_by_user", "obsolete"):
                state = "purchased" if owned["state"] == "purchased" else "removed_by_user"
            elif owned["state"] == "synced" and owned["applied_spec"] == item["spec"]:
                state = "synced"
            else:
                state = "pending"
        items.append(
            ShoppingItem(
                id=rid,
                name=item["name"],
                spec=item["spec"],
                sources=len(item["sources"]),
                state=state,
            )
        )

    def job(key):
        value = jobs.get(key, {})
        return value.get("state", "idle"), public_error(value.get("error_code"))

    job_state, error = job("shopping.current")
    verify_state, verify_error = job("bring.verify")
    return ShoppingSnapshot(
        period=monday,
        calculated_at=time.time(),
        planned_meals=meal_count,
        excluded_staples=excluded,
        requirements=sorted(items, key=lambda i: (normalise(i.name), i.spec, i.id)),
        last_success_at=success_at,
        job_state=job_state,
        error_code=error,
        verification_state=verify_state,
        verification_error=verify_error,
        list_id=list_id,
        list_name=config.get("list_name"),
        connection_state="not_configured"
        if not raw
        else "list_not_selected"
        if not list_id
        else "ready"
        if ready
        else "compatibility_unverified",
    )


def request_verification(database, body):
    raw = settings(database)
    config = json.loads(raw) if raw else {}
    if config.get("list_id") != str(body.list_id):
        raise DomainError("bring_configuration_changed", 409)
    with database.transaction() as db:
        existing = db.execute(
            "SELECT * FROM background_job WHERE dedupe_key='bring.verify'"
        ).fetchone()
        if existing and existing["state"] in ("queued", "running"):
            return {"state": existing["state"]}
        if not rate_limit(db, "bring.verify", 3, 3600):
            raise DomainError("bring_verification_rate_limited", 429)
        iid, item = str(uuid4()), str(uuid4())
        db.execute(
            "INSERT INTO bring_probe (id,list_id,configuration_hash,item_id,name,created_at) VALUES (?,?,?,?,?,?)",
            (
                iid,
                str(body.list_id),
                configuration_hash(raw),
                item,
                "mealf-test-" + item,
                time.time(),
            ),
        )
        enqueue(db, "bring.verify", "bring.verify", {"id": iid})
    return {"state": "queued"}
