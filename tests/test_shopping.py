import json
import time
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from aircooker.bring import Capabilities, Item, reconcile
from aircooker.bring_runtime import UnofficialBringConnector
from aircooker.bring_verification import verify
from aircooker.db import Database
from aircooker.errors import DomainError
from aircooker.jobs import claim, finish
from aircooker.planning import week_start
from aircooker.secrets import SecretVault
from aircooker.shopping import BringVerification, configuration_hash, request_verification, snapshot


class Connector:
    capabilities = Capabilities(True, True, True, True)

    def __init__(self):
        self.items = {"manual": Item("manual", "Apples", "my own")}
        self.operations = []
        self.runner = SimpleNamespace(close=lambda: None)
        self.drop_response = False
        self.rewrite_uuid = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, list_id):
        return list(self.items.values())

    def probe_write(self, list_id, item, action):
        iid = "unexpected" if self.rewrite_uuid else item.id
        self.operations.append((action, iid))
        if action == "remove":
            self.items.pop(iid, None)
        else:
            self.items[iid] = Item(iid, item.name, item.spec, action == "complete")
        if self.drop_response:
            self.drop_response = False
            raise TimeoutError("synthetic response dropped")

    def add(self, list_id, item):
        self.probe_write(list_id, item, "add")

    update = add

    def remove(self, list_id, item):
        self.probe_write(list_id, item, "remove")


def configure(db):
    list_id = str(uuid4())
    raw = json.dumps(
        {
            "email": "synthetic@example.invalid",
            "password": "synthetic-secret",
            "list_id": list_id,
            "list_name": "Synthetic test list",
        }
    )
    SecretVault(db.root / "config").save("bring", raw)
    return list_id


def prepare(db, list_id):
    request_verification(db, BringVerification(list_id=list_id, dedicated_test_list_confirmed=True))
    with db.connect() as sql:
        return json.loads(
            sql.execute(
                "SELECT payload FROM background_job WHERE dedupe_key='bring.verify'"
            ).fetchone()[0]
        )["id"]


def test_probe_preserves_manual_item_then_enables_only_exact_configuration(tmp_path):
    db = Database(tmp_path)
    lid = configure(db)
    connector = Connector()
    iid = prepare(db, lid)
    verify(db, lambda _: connector, iid)
    assert connector.items == {"manual": Item("manual", "Apples", "my own")}
    assert [x[0] for x in connector.operations] == ["add", "add", "add", "complete", "remove"]
    assert len({x[1] for x in connector.operations}) == 1
    live = UnofficialBringConnector(tmp_path / "config")
    assert live.capabilities.uuid_create
    live.runner.close()
    vault = SecretVault(tmp_path / "config")
    raw = json.loads(vault.load("bring"))
    raw["password"] = "changed"
    vault.save("bring", json.dumps(raw))
    live = UnofficialBringConnector(tmp_path / "config")
    assert not live.capabilities.uuid_create
    live.runner.close()
    with db.connect() as sql:
        job = sql.execute(
            "SELECT payload FROM background_job WHERE dedupe_key='bring.verify'"
        ).fetchone()[0]
    assert "synthetic-secret" not in job and "password" not in job


def test_interrupted_probe_restarts_with_same_uuid_and_preserves_baseline(tmp_path):
    db = Database(tmp_path)
    lid = configure(db)
    connector = Connector()
    iid = prepare(db, lid)
    connector.drop_response = True
    with pytest.raises(TimeoutError):
        verify(db, lambda _: connector, iid)
    first_id = connector.operations[0][1]
    verify(Database(tmp_path), lambda _: connector, iid)
    assert all(item == first_id for _, item in connector.operations)
    assert set(connector.items) == {"manual"}
    count = len(connector.operations)
    verify(db, lambda _: connector, iid)
    assert len(connector.operations) == count


def test_uuid_rewrite_never_removes_unknown_item_and_fails_closed(tmp_path):
    db = Database(tmp_path)
    lid = configure(db)
    connector = Connector()
    connector.rewrite_uuid = True
    iid = prepare(db, lid)
    job = claim(db)
    with pytest.raises(DomainError, match="bring_uuid_not_supported") as error:
        verify(db, lambda _: connector, iid)
    assert error.value.terminal
    finish(db, job, error.value.code, terminal=error.value.terminal)
    assert connector.operations == [("add", "unexpected")]
    assert connector.items["manual"].spec == "my own"
    assert not (tmp_path / "config/bring-compatibility.json").exists()
    with db.connect() as sql:
        assert (
            sql.execute(
                "SELECT attempts FROM background_job WHERE dedupe_key='bring.verify'"
            ).fetchone()[0]
            == 1
        )


def test_configuration_change_stops_old_probe_without_mutations(tmp_path):
    db = Database(tmp_path)
    lid = configure(db)
    connector = Connector()
    iid = prepare(db, lid)
    configure(db)
    with pytest.raises(DomainError, match="bring_configuration_changed"):
        verify(db, lambda _: connector, iid)
    assert connector.operations == []


def test_concurrent_manual_change_is_never_restored(tmp_path):
    db = Database(tmp_path)
    lid = configure(db)
    connector = Connector()
    iid = prepare(db, lid)
    original = connector.probe_write

    def write(*args):
        original(*args)
        connector.items["manual"] = Item("manual", "Apples", "human changed")

    connector.probe_write = write
    with pytest.raises(DomainError, match="bring_verification_baseline_changed"):
        verify(db, lambda _: connector, iid)
    assert connector.items["manual"].spec == "human changed"
    assert len(connector.operations) == 1


@pytest.mark.parametrize(
    "body", [{}, {"list_id": str(uuid4()), "dedicated_test_list_confirmed": False}]
)
def test_probe_requires_explicit_dedicated_list_confirmation(harness, body):
    client, _, _, _ = harness
    assert client.post("/api/v1/integrations/bring/verify", json=body).status_code == 422


def test_snapshot_current_week_scaling_pantry_leftovers_and_states(harness, mutation):
    client, app, device, _ = harness
    db = app.state.database
    lid = configure(db)
    connector = Connector()
    day = str(week_start(datetime.now(ZoneInfo("Europe/Zurich")).date()))
    rid = str(uuid4())
    pantryid = str(uuid4())
    mealid = str(uuid4())
    recipe = {
        "title": "Synthetic rice",
        "servings": "2",
        "ingredients": [
            {"id": str(uuid4()), "name": "Rice", "quantity": "200", "unit": "g"},
            {
                "id": str(uuid4()),
                "name": "Salt",
                "quantity": None,
                "unit": "",
                "original_text": "to taste",
            },
        ],
        "steps": ["Cook"],
    }
    mutations = [
        mutation(device, entity_id=rid, payload=recipe),
        mutation(
            device,
            kind="pantry",
            entity_id=pantryid,
            payload={"name": "Salt", "available": True, "include_this_week": False},
        ),
        mutation(
            device,
            kind="meal",
            entity_id=mealid,
            payload={"recipe_id": rid, "date": day, "category": "dinner", "servings": "4"},
        ),
    ]
    response = client.post("/api/v1/sync/push", json={"mutations": mutations})
    assert response.status_code == 200, response.text
    value = snapshot(db, lambda _: connector)
    assert value.planned_meals == 1 and value.excluded_staples == ["Salt"]
    assert [(i.name, i.spec, i.state) for i in value.requirements] == [
        ("Rice", "400 g", "not_sent")
    ]
    desired = {value.requirements[0].id: {"name": "Rice", "spec": "400 g"}}
    reconcile(db, connector, lid, day, desired)
    assert snapshot(db, lambda _: connector).requirements[0].state == "synced"
    item = next(i for i in connector.items.values() if i.name == "Rice")
    connector.items[item.id] = Item(item.id, item.name, item.spec, True)
    reconcile(db, connector, lid, day, desired)
    assert snapshot(db, lambda _: connector).requirements[0].state == "purchased"
    with db.transaction() as sql:
        sql.execute(
            "UPDATE background_job SET error_code='private_provider_credential' WHERE dedupe_key='shopping.current'"
        )
    assert snapshot(db, lambda _: connector).error_code == "operation_failed"
    assert client.get("/api/v1/planning/shopping").status_code == 200


def test_snapshot_manual_match_not_adopted(harness, mutation):
    client, app, device, _ = harness
    db = app.state.database
    lid = configure(db)
    connector = Connector()
    day = str(week_start(datetime.now(ZoneInfo("Europe/Zurich")).date()))
    rid = str(uuid4())
    for kind, eid, payload in [
        (
            "recipe",
            rid,
            {
                "title": "Apples",
                "servings": "2",
                "ingredients": [
                    {"id": str(uuid4()), "name": "Apples", "quantity": "2", "unit": "piece"}
                ],
                "steps": ["Slice"],
            },
        ),
        (
            "meal",
            str(uuid4()),
            {"recipe_id": rid, "date": day, "category": "lunch", "servings": "2"},
        ),
    ]:
        assert (
            client.post(
                "/api/v1/sync/push",
                json={"mutations": [mutation(device, kind=kind, entity_id=eid, payload=payload)]},
            ).status_code
            == 200
        )
    value = snapshot(db, lambda _: connector)
    reconcile(
        db,
        connector,
        lid,
        day,
        {i.id: {"name": i.name, "spec": i.spec} for i in value.requirements},
    )
    assert snapshot(db, lambda _: connector).requirements[0].state == "manual"
    assert connector.operations == []


def test_public_snapshot_authentication_and_no_credentials(harness):
    client, app, _, _ = harness
    configure(app.state.database)
    result = client.get("/api/v1/planning/shopping")
    assert result.status_code == 200
    assert result.json()["connection_state"] == "compatibility_unverified"
    assert "synthetic-secret" not in result.text and "configuration_hash" not in result.text
    client.headers.pop("Authorization")
    assert client.get("/api/v1/planning/shopping").status_code == 401


def test_corrupt_or_expired_report_fails_closed(tmp_path):
    db = Database(tmp_path)
    lid = configure(db)
    raw = SecretVault(tmp_path / "config").load("bring")
    path = tmp_path / "config/bring-compatibility.json"
    for content in [
        "not-json",
        "[]",
        json.dumps(
            {
                "sdk_version": "1.1.2",
                "list_id": lid,
                "passed": True,
                "configuration_hash": configuration_hash(raw),
                "verified_at": "bad",
            }
        ),
        json.dumps(
            {
                "sdk_version": "1.1.2",
                "list_id": lid,
                "passed": True,
                "configuration_hash": configuration_hash(raw),
                "verified_at": time.time() - 31 * 86400,
            }
        ),
    ]:
        path.write_text(content)
        c = UnofficialBringConnector(tmp_path / "config")
        assert not c.capabilities.uuid_create
        c.runner.close()


@pytest.mark.parametrize("operation", ["add", "remove"])
def test_remote_acknowledgement_failure_revokes_capability_evidence(tmp_path, operation):
    db = Database(tmp_path)
    configure(db)
    report = tmp_path / "config/bring-compatibility.json"
    report.write_text("{}")
    connector = UnofficialBringConnector(tmp_path / "config")
    connector.capabilities = Capabilities(True, True, True, True)
    connector.bring = object()
    writes = []
    connector._send = lambda *args: writes.append(args)
    own = Item("persisted-owned-uuid", "Tomatoes", "4 piece")
    connector.read = lambda _: [Item("manual", "Apples", "my own")] if operation == "add" else [own]
    try:
        with pytest.raises(DomainError, match="bring_write_not_confirmed"):
            getattr(connector, operation)("selected-list", own)
        assert len(writes) == 1 and writes[0][1].id == own.id
        assert not report.exists()
    finally:
        connector.runner.close()


def test_verification_rejects_unselected_list_and_limits_explicit_retries(tmp_path):
    db = Database(tmp_path)
    lid = configure(db)
    with pytest.raises(DomainError, match="bring_configuration_changed"):
        prepare(db, str(uuid4()))
    for _ in range(3):
        prepare(db, lid)
        with db.transaction() as sql:
            sql.execute("UPDATE background_job SET state='failed' WHERE dedupe_key='bring.verify'")
    with pytest.raises(DomainError, match="bring_verification_rate_limited"):
        prepare(db, lid)
