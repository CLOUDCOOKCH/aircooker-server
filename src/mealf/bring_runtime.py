"""Isolated adapter for MIT-licensed bring-api 1.1.2; never uses name-only writes."""

import asyncio
import json
import time
from pathlib import Path

import aiohttp
from bring_api import Bring
from bring_api.types import BringItemOperation

from .bring import Capabilities, Item
from .errors import DomainError
from .secrets import SecretVault
from .shopping import configuration_hash


class UnofficialBringConnector:
    def __init__(self, root: Path):
        self.root = root
        self.vault = SecretVault(root)
        raw = self.vault.load("bring")
        if not raw:
            raise DomainError("bring_not_configured", 409)
        self.settings = json.loads(raw)
        self.capabilities = Capabilities()
        report = root / "bring-compatibility.json"
        if report.exists():
            try:
                data = json.loads(report.read_text())
            except (ValueError, OSError):
                data = {}
            if (
                isinstance(data, dict)
                and data.get("sdk_version") == "1.1.2"
                and data.get("configuration_hash") == configuration_hash(raw, root)
                and data.get("list_id") == self.settings.get("list_id")
                and isinstance(data.get("verified_at"), (int, float))
                and 0 <= time.time() - data["verified_at"] < 30 * 86400
                and data.get("passed") is True
            ):
                self.capabilities = Capabilities(True, True, True, True)
        self.runner = asyncio.Runner()
        self.session: aiohttp.ClientSession | None = None
        self.bring: Bring | None = None

    async def start(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        self.bring = Bring(self.session, self.settings["email"], self.settings["password"])
        await self.bring.login()
        await self.bring.load_lists()

    def __enter__(self):
        try:
            self.runner.run(self.start())
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        if self.session:
            self.runner.run(self.session.close())
        self.runner.close()

    def read(self, list_id):
        assert self.bring is not None
        response = self.runner.run(self.bring.get_list(list_id))
        items = [
            Item(item.uuid, item.itemId, item.specification, completed)
            for completed, group in [
                (False, response.items.purchase),
                (True, response.items.recently),
            ]
            for item in group
        ]
        if any(not item.id for item in items) or len({i.id for i in items}) != len(items):
            raise DomainError("bring_item_identity_invalid", 502)
        return items

    def probe_write(self, list_id, item, action):
        """Only the explicit dedicated-list experiment calls this with its persisted UUID."""
        operation = {
            "add": BringItemOperation.ADD,
            "complete": BringItemOperation.COMPLETE,
            "remove": BringItemOperation.REMOVE,
        }[action]
        self._send(list_id, item, operation)

    def _send(self, list_id, item, operation):
        assert self.bring is not None
        self.runner.run(
            self.bring.batch_update_list(
                list_id, {"uuid": item.id, "itemId": item.name, "spec": item.spec}, operation
            )
        )

    def _write(self, list_id, item, operation):
        assert self.bring is not None
        if not self.capabilities.uuid_create or not item.id:
            raise DomainError("bring_capability_unverified", 409)
        self._send(list_id, item, operation)
        actual = {i.id: i for i in self.read(list_id)}
        found = actual.get(item.id)
        valid = (
            found is None
            if operation == BringItemOperation.REMOVE
            else (
                found is not None
                and found.name == item.name
                and found.spec == item.spec
                and not found.completed
            )
        )
        if not valid:
            (self.root / "bring-compatibility.json").unlink(missing_ok=True)
            raise DomainError("bring_write_not_confirmed", 502)

    def add(self, list_id, item):
        self._write(list_id, item, BringItemOperation.ADD)

    update = add

    def remove(self, list_id, item):
        self._write(list_id, item, BringItemOperation.REMOVE)

    def lists(self):
        assert self.bring is not None
        response = self.runner.run(self.bring.load_lists())
        return [{"id": item.listUuid, "name": item.name} for item in response.lists]
