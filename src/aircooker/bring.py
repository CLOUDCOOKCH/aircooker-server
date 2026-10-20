import time
from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from .errors import DomainError
from .planning import normalise


@dataclass(frozen=True)
class Capabilities:
    uuid_create: bool = False
    uuid_update: bool = False
    uuid_remove: bool = False
    completed_status: bool = False


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    spec: str
    completed: bool = False


class BringConnector(Protocol):
    capabilities: Capabilities

    def read(self, list_id: str) -> list[Item]: ...
    def add(self, list_id: str, item: Item) -> None: ...
    def update(self, list_id: str, item: Item) -> None: ...
    def remove(self, list_id: str, item: Item) -> None: ...


class DisabledConnector:
    capabilities = Capabilities()

    def read(self, list_id):
        raise DomainError("bring_not_configured", 409)

    def add(self, *args):
        raise DomainError("bring_capability_unverified", 409)

    update = add
    remove = add


def reconcile(database, connector: BringConnector, list_id: str, period: str, desired: dict):
    cap = connector.capabilities
    if not all((cap.uuid_create, cap.uuid_update, cap.uuid_remove, cap.completed_status)):
        raise DomainError("bring_capability_unverified", 409)
    actual = {item.id: item for item in connector.read(list_id)}
    # Caller serialises reconciliations through the single durable worker.
    with database.connect() as db:
        ledger = [
            dict(r)
            for r in db.execute("SELECT * FROM bring_owned_item WHERE list_id=?", (list_id,))
        ]
    owned_ids = {r["item_id"] for r in ledger}
    manual_names = {normalise(i.name) for i in actual.values() if i.id not in owned_ids}
    for row in ledger:
        item = actual.get(row["item_id"])
        if item and item.completed:
            with database.transaction() as db:
                db.execute(
                    "UPDATE bring_owned_item SET state='purchased',reconciled_at=? WHERE item_id=?",
                    (time.time(), item.id),
                )
            row["state"] = "purchased"
        if row["state"] == "purchased":
            continue
        wanted = desired.get(row["requirement_id"]) if row["period"] == period else None
        # Respect manual deletions too. Missing previously applied items are not resurrected.
        if item is None and row["applied_spec"] is not None:
            with database.transaction() as db:
                db.execute(
                    "UPDATE bring_owned_item SET state='removed_by_user' WHERE item_id=?",
                    (row["item_id"],),
                )
            continue
        if wanted is None:
            if item:
                # UUID is always taken from persisted ownership, never from a name match.
                connector.remove(list_id, item)
            with database.transaction() as db:
                db.execute(
                    "UPDATE bring_owned_item SET state='obsolete',reconciled_at=? WHERE item_id=?",
                    (time.time(), row["item_id"]),
                )
            continue
        if row["state"] in ("removed_by_user", "obsolete"):
            continue
        target = Item(row["item_id"], row["name"], wanted["spec"])
        if item is None:
            connector.add(list_id, target)
        elif item.spec != target.spec:
            connector.update(list_id, target)
        with database.transaction() as db:
            db.execute(
                "UPDATE bring_owned_item SET state='synced',spec=?,applied_spec=?,reconciled_at=? WHERE item_id=?",
                (target.spec, target.spec, time.time(), target.id),
            )
    existing = {r["requirement_id"] for r in ledger if r["period"] == period}
    for rid, wanted in desired.items():
        if rid in existing or normalise(wanted["name"]) in manual_names:
            continue
        item = Item(str(uuid4()), wanted["name"], wanted["spec"])
        # Persist identity BEFORE the external operation: a crash retries the same UUID.
        with database.transaction() as db:
            db.execute(
                "INSERT INTO bring_owned_item VALUES (?,?,?,?,?,?,'pending',NULL,NULL)",
                (period, rid, list_id, item.id, item.name, item.spec),
            )
        connector.add(list_id, item)
        with database.transaction() as db:
            db.execute(
                "UPDATE bring_owned_item SET state='synced',applied_spec=?,reconciled_at=? WHERE item_id=?",
                (item.spec, time.time(), item.id),
            )
    return {"state": "synced", "period": period}
