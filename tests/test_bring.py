import pytest

from aircooker.bring import Capabilities, Item, reconcile
from aircooker.db import Database
from aircooker.errors import DomainError


class Connector:
    capabilities = Capabilities(True, True, True, True)

    def __init__(self):
        self.items = {}
        self.operations = []
        self.fail_after_add = False

    def read(self, list_id):
        return list(self.items.values())

    def add(self, list_id, item):
        self.items[item.id] = item
        self.operations.append(("add", item.id))
        if self.fail_after_add:
            self.fail_after_add = False
            raise TimeoutError("simulated response lost after remote commit")

    def update(self, list_id, item):
        self.items[item.id] = item
        self.operations.append(("update", item.id))

    def remove(self, list_id, item):
        del self.items[item.id]
        self.operations.append(("remove", item.id))


def desired(spec="200 g", name="Flour"):
    return {"flour": {"name": name, "spec": spec}}


def test_never_deletes_or_overwrites_manual_items(tmp_path):
    database = Database(tmp_path)
    connector = Connector()
    connector.items["manual"] = Item("manual", "Flour", "my special flour")
    reconcile(database, connector, "test", "2026-10-19", desired())
    reconcile(database, connector, "test", "2026-10-19", {})
    assert connector.items["manual"].spec == "my special flour"
    assert connector.operations == []


def test_owned_update_removal_and_idempotence(tmp_path):
    database = Database(tmp_path)
    connector = Connector()
    connector.items["manual"] = Item("manual", "Apples", "2")
    reconcile(database, connector, "test", "2026-10-19", desired())
    reconcile(database, connector, "test", "2026-10-19", desired())
    assert len(connector.operations) == 1
    reconcile(database, connector, "test", "2026-10-19", desired("400 g"))
    assert connector.operations[-1][0] == "update"
    reconcile(database, connector, "test", "2026-10-19", {})
    assert set(connector.items) == {"manual"}


def test_partial_failure_reuses_persisted_uuid(tmp_path):
    database = Database(tmp_path)
    connector = Connector()
    connector.fail_after_add = True
    with pytest.raises(TimeoutError):
        reconcile(database, connector, "test", "2026-10-19", desired())
    original = set(connector.items)
    reconcile(database, connector, "test", "2026-10-19", desired())
    assert set(connector.items) == original
    assert len(connector.operations) == 1


def test_purchased_item_not_resurrected_and_new_week_independent(tmp_path):
    database = Database(tmp_path)
    connector = Connector()
    reconcile(database, connector, "test", "2026-10-19", desired())
    item = next(iter(connector.items.values()))
    connector.items[item.id] = Item(item.id, item.name, item.spec, True)
    reconcile(database, connector, "test", "2026-10-19", desired("400 g"))
    del connector.items[item.id]
    reconcile(database, connector, "test", "2026-10-19", desired())
    assert not connector.items
    reconcile(database, connector, "test", "2026-10-26", desired())
    assert len(connector.items) == 1 and item.id not in connector.items


def test_capabilities_fail_closed(tmp_path):
    database = Database(tmp_path)
    connector = Connector()
    connector.capabilities = Capabilities()
    with pytest.raises(DomainError, match="bring_capability_unverified"):
        reconcile(database, connector, "test", "2026-10-19", desired())
    assert not connector.operations
