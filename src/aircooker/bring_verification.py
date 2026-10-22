"""Explicit dedicated-list capability experiment, persisted across worker restarts."""

import hashlib
import json
import os
import time
from uuid import uuid4

from .bring import Item
from .errors import DomainError
from .jobs import enqueue
from .shopping import configuration_hash, settings


def fingerprint(item):
    return hashlib.sha256(json.dumps([item.name, item.spec, item.completed]).encode()).hexdigest()


class BringVerificationBlocked(DomainError):
    terminal = True


def verify(database, connector_factory, iid):
    try:
        return _verify(database, connector_factory, iid)
    except DomainError as exc:
        if exc.code in {
            "bring_configuration_changed",
            "bring_uuid_not_supported",
            "bring_verification_unsafe",
            "bring_verification_baseline_changed",
        }:
            raise BringVerificationBlocked(exc.code, exc.status) from exc
        raise


def _verify(database, connector_factory, iid):
    root = database.root / "config"
    with database.connect() as db:
        row = db.execute("SELECT * FROM bring_probe WHERE id=?", (iid,)).fetchone()
    if not row:
        raise DomainError("bring_verification_missing", 409)
    if row["completed_at"] is not None:
        return
    raw = settings(database)
    if not raw or configuration_hash(raw) != row["configuration_hash"]:
        raise DomainError("bring_configuration_changed", 409)
    list_id, own_id, name = row["list_id"], row["item_id"], row["name"]
    with connector_factory(root) as connector:
        current = {i.id: i for i in connector.read(list_id)}
        baseline = json.loads(row["baseline"]) if row["baseline"] is not None else None
        if baseline is None:
            if (
                own_id in current
                or any(i.name == name for i in current.values())
                or len(current) > 2000
            ):
                raise DomainError("bring_verification_unsafe", 409)
            baseline = {k: fingerprint(v) for k, v in current.items()}
            with database.transaction() as db:
                db.execute(
                    "UPDATE bring_probe SET baseline=? WHERE id=?", (json.dumps(baseline), iid)
                )
        operations = [
            ("add", "one"),
            ("add", "one"),
            ("add", "two"),
            ("complete", "two"),
            ("remove", "two"),
        ]
        deadline = time.monotonic() + 90
        for stage in range(row["stage"], len(operations)):
            if time.monotonic() > deadline:
                raise DomainError("bring_verification_timeout", 503)
            if settings(database) != raw:
                raise DomainError("bring_configuration_changed", 409)
            action, spec = operations[stage]
            connector.probe_write(list_id, Item(own_id, name, spec), action)
            actual = {i.id: i for i in connector.read(list_id)}
            # Never restore/overwrite a baseline item: concurrent human changes fail the check.
            if any(k not in actual or fingerprint(actual[k]) != v for k, v in baseline.items()):
                raise DomainError("bring_verification_baseline_changed", 409)
            own = actual.get(own_id)
            if action == "remove":
                valid = own is None
            else:
                valid = bool(
                    own
                    and own.name == name
                    and own.spec == spec
                    and own.completed == (action == "complete")
                )
                valid = valid and sum(i.name == name for i in actual.values()) == 1
            if not valid:
                # Do not remove an unidentified response item based on its matching name.
                raise DomainError("bring_uuid_not_supported", 409)
            with database.transaction() as db:
                db.execute("UPDATE bring_probe SET stage=? WHERE id=?", (stage + 1, iid))
    if settings(database) != raw:
        raise DomainError("bring_configuration_changed", 409)
    report = {
        "sdk_version": "1.1.2",
        "list_id": list_id,
        "verified_at": time.time(),
        "passed": True,
        "configuration_hash": configuration_hash(raw),
    }
    temporary = root / ("bring-compatibility-" + str(uuid4()) + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w") as out:
            json.dump(report, out)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, root / "bring-compatibility.json")
    finally:
        temporary.unlink(missing_ok=True)
    with database.transaction() as db:
        db.execute("UPDATE bring_probe SET completed_at=? WHERE id=?", (time.time(), iid))
        enqueue(db, "shopping.reconcile", "shopping.current", {})
