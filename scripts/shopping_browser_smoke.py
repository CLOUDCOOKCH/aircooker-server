"""Real PWA/SQLite/worker flows with an explicit in-memory Bring service double."""

import json
import os
import shutil
import socket
import threading
import time
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
import uvicorn
from bring_api.types import BringItemOperation
from playwright.sync_api import expect, sync_playwright

from mealf.app import create_app
from mealf.bring import Item
from mealf.bring_runtime import UnofficialBringConnector
from mealf.errors import DomainError
from mealf.planning import week_start
from mealf.secrets import SecretVault


class SyntheticBring(UnofficialBringConnector):
    items = {"manual": Item("manual", "Rice", "my own rice")}
    writes = []
    fail_recipe_writes = True

    def __enter__(self):
        self.bring = object()  # Explicit SDK transport double, no network client.
        return self

    def __exit__(self, *args):
        self.runner.close()

    def read(self, list_id):
        return list(self.items.values())

    def _send(self, list_id, item, operation):
        if not item.name.startswith("mealf-test-") and self.fail_recipe_writes:
            raise DomainError("bring_connection_failed", 502)
        self.writes.append((operation, item.id))
        if operation == BringItemOperation.REMOVE:
            self.items.pop(item.id, None)
        else:
            self.items[item.id] = Item(
                item.id, item.name, item.spec, operation == BringItemOperation.COMPLETE
            )


def main():
    captures = Path(os.environ.get("MEALF_SHOPPING_SCREENSHOT_DIR", "build/shopping-browser"))
    captures.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="mealf-shopping-browser-") as directory:
        root = Path(directory)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        os.environ["LOG_SETUP_TOKEN"] = "false"
        with patch("mealf.app.UnofficialBringConnector", SyntheticBring):
            app = create_app(root)
            lid = str(uuid4())
            SecretVault(root / "config").save(
                "bring",
                json.dumps(
                    {
                        "email": "synthetic@example.invalid",
                        "password": "synthetic-only",
                        "list_id": lid,
                        "list_name": "Synthetic Bring test list",
                    }
                ),
            )
            server = uvicorn.Server(
                uvicorn.Config(
                    app, host="127.0.0.1", port=port, log_level="error", access_log=False
                )
            )
            thread = threading.Thread(target=server.run, daemon=True)
            thread.start()
            try:
                for _ in range(100):
                    if server.started:
                        break
                    time.sleep(0.05)
                assert server.started
                with httpx.Client(base_url=base, trust_env=False, timeout=15) as operator:
                    device = str(uuid4())
                    auth = operator.post(
                        "/api/v1/setup",
                        headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
                        json={
                            "name": "Synthetic shopping kitchen",
                            "username": "cook",
                            "password": "synthetic browser password",
                            "timezone": "Europe/Zurich",
                            "device_id": device,
                        },
                    )
                    auth.raise_for_status()
                    operator.headers["Authorization"] = "Bearer " + auth.json()["access_token"]
                    monday = str(week_start(datetime.now(ZoneInfo("Europe/Zurich")).date()))
                    rid = str(uuid4())
                    values = [
                        (
                            "recipe",
                            rid,
                            {
                                "title": "Synthetic tomato rice",
                                "servings": "2",
                                "ingredients": [
                                    {
                                        "id": str(uuid4()),
                                        "name": "Rice",
                                        "quantity": "200",
                                        "unit": "g",
                                    },
                                    {
                                        "id": str(uuid4()),
                                        "name": "Tomatoes",
                                        "quantity": "2",
                                        "unit": "piece",
                                    },
                                    {
                                        "id": str(uuid4()),
                                        "name": "Salt",
                                        "quantity": None,
                                        "unit": "",
                                        "original_text": "to taste",
                                    },
                                ],
                                "steps": ["Cook"],
                            },
                        ),
                        (
                            "pantry",
                            str(uuid4()),
                            {"name": "Salt", "available": True, "include_this_week": False},
                        ),
                        (
                            "meal",
                            str(uuid4()),
                            {
                                "recipe_id": rid,
                                "date": monday,
                                "category": "dinner",
                                "servings": "4",
                            },
                        ),
                    ]
                    for kind, eid, payload in values:
                        mid = str(uuid4())
                        response = operator.post(
                            "/api/v1/sync/push",
                            json={
                                "mutations": [
                                    {
                                        "mutation_id": mid,
                                        "idempotency_key": mid,
                                        "kind": kind,
                                        "entity_id": eid,
                                        "device_id": device,
                                        "operation": "upsert",
                                        "base_revision": 0,
                                        "client_timestamp": "2000-01-01T00:00:00Z",
                                        "payload": payload,
                                    }
                                ]
                            },
                        )
                        response.raise_for_status()
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(
                            executable_path=os.environ.get("CHROMIUM_EXECUTABLE")
                            or shutil.which("chromium")
                            or shutil.which("google-chrome"),
                            args=["--no-sandbox"],
                        )
                        context = browser.new_context(viewport={"width": 1440, "height": 1000})
                        page = context.new_page()
                        page.set_default_timeout(15000)
                        errors = []
                        page.on("pageerror", lambda e: errors.append(str(e)))
                        page.goto(base + "/app/")
                        page.get_by_role("button", name="Open your kitchen", exact=True).click()
                        page.get_by_label("Username", exact=True).fill("cook")
                        page.get_by_label("Password", exact=True).fill("synthetic browser password")
                        page.get_by_role("button", name="Sign in", exact=True).click()
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Calendar", exact=True
                        ).click()
                        # The calendar shortcut and primary navigation open the same destination.
                        page.locator("main").get_by_role(
                            "button", name="Shopping list", exact=True
                        ).click()
                        shopping_nav = page.get_by_role("navigation").get_by_role(
                            "button", name="Shopping list", exact=True
                        )
                        expect(shopping_nav).to_have_attribute("aria-current", "page")
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Recipes", exact=True
                        ).click()
                        shopping_nav.focus()
                        shopping_nav.press("Enter")
                        expect(shopping_nav).to_have_attribute("aria-current", "page")
                        expect(
                            page.get_by_role("navigation").locator('[aria-current="page"]')
                        ).to_have_count(1)
                        expect(
                            page.get_by_role("heading", name="Shopping list", exact=True)
                        ).to_be_visible()
                        expect(page.get_by_text("400 g", exact=True)).to_be_visible()
                        expect(
                            page.get_by_role("button", name="Sync to Bring!", exact=True)
                        ).to_be_disabled()
                        page.get_by_role("heading", name="Shopping list", exact=True).click()
                        page.screenshot(
                            path=str(captures / "shopping-unverified-desktop.png"), full_page=True
                        )
                        page.get_by_text("Verify Bring! compatibility", exact=True).click()
                        page.get_by_role("checkbox").check()
                        page.get_by_role(
                            "button", name="Verify selected test list", exact=True
                        ).click()
                        expect(
                            page.get_by_text("Bring! could not finish this operation.", exact=False)
                        ).to_be_visible(timeout=20000)
                        SyntheticBring.fail_recipe_writes = False
                        with page.expect_request(
                            lambda req: req.method == "POST"
                            and req.url.endswith("/api/v1/integrations/bring/reconcile")
                        ):
                            page.get_by_role("button", name="Sync to Bring!", exact=True).click()
                        expect(page.get_by_text("Synced to Bring!", exact=True)).to_be_visible(
                            timeout=20000
                        )
                        expect(
                            page.get_by_text("Already in Bring! · left unchanged", exact=True)
                        ).to_be_visible()
                        assert SyntheticBring.items["manual"] == Item(
                            "manual", "Rice", "my own rice"
                        )
                        assert (
                            len([i for i in SyntheticBring.items.values() if i.name == "Tomatoes"])
                            == 1
                        )
                        page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                        assert not page.evaluate(
                            "async()=> (await axe.run(document.querySelector('main'), {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                        )
                        page.screenshot(
                            path=str(captures / "shopping-synced-desktop.png"), full_page=True
                        )
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Settings", exact=True
                        ).click()
                        page.get_by_label("Language", exact=True).select_option("de")
                        page.evaluate("window.mealfAppearance.set('after-dark')")
                        page.set_viewport_size({"width": 390, "height": 844})
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Einkaufsliste", exact=True
                        ).click()
                        expect(
                            page.get_by_text("Mit Bring! abgeglichen", exact=True)
                        ).to_be_visible()
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                        page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                        assert not page.evaluate(
                            "async()=> (await axe.run(document.querySelector('main'), {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                        )
                        page.screenshot(
                            path=str(captures / "shopping-synced-phone-de-dark.png"), full_page=True
                        )
                        # All six destinations keep distinct, usable hit areas at 320px.
                        page.set_viewport_size({"width": 320, "height": 740})
                        assert page.evaluate("""() => {
                          const nav = document.querySelector('.nav-links');
                          const boxes = [...nav.querySelectorAll('button')].map(b => b.getBoundingClientRect());
                          return boxes.length === 6 && boxes.every((b, i) =>
                            b.width >= 44 && b.height >= 44 && b.left >= 0 && b.right <= innerWidth &&
                            (!i || b.left >= boxes[i - 1].right)) &&
                            [...nav.querySelectorAll('button span')].every(s => s.scrollWidth <= s.clientWidth + 1 &&
                              s.clientHeight <= parseFloat(getComputedStyle(s).lineHeight) + 1) &&
                            document.documentElement.scrollWidth <= innerWidth;
                        }""")
                        expect(
                            page.get_by_role("navigation").get_by_role(
                                "button", name="Einkaufsliste", exact=True
                            )
                        ).to_have_attribute("aria-current", "page")
                        page.screenshot(
                            path=str(captures / "shopping-nav-phone-320-de-dark.png"),
                            full_page=True,
                        )
                        page.set_viewport_size({"width": 390, "height": 844})
                        page.evaluate("async()=>{await navigator.serviceWorker.ready}")
                        context.set_offline(True)
                        page.reload()
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Kalender", exact=True
                        ).click()
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Einkaufsliste", exact=True
                        ).click()
                        expect(page.get_by_text("400 g", exact=True)).to_be_visible()
                        expect(
                            page.get_by_role(
                                "button", name="Mit Bring! synchronisieren", exact=True
                            )
                        ).to_be_disabled()
                        expect(
                            page.get_by_text("Gespeicherte Serverberechnung;", exact=False)
                        ).to_be_visible()
                        page.screenshot(
                            path=str(captures / "shopping-offline-phone-de-dark.png"),
                            full_page=True,
                        )
                        assert not errors, errors
                        browser.close()
            finally:
                server.should_exit = True
                thread.join(timeout=20)
                assert not thread.is_alive()
    print(
        "PASS: real PWA/server/worker shopping projection, explicit dedicated-list verification, failed/successful manual sync, manual-item preservation, EN desktop/DE dark phone/Axe and offline cached reload. Bring service responses are synthetic; no live Bring mutation or physical iPhone evidence."
    )


if __name__ == "__main__":
    main()
