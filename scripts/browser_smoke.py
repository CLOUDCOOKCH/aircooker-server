"""Chromium E2E on loopback with synthetic data and explicit test-only adapters.

Install requirements-browser.lock; set CHROMIUM_EXECUTABLE if Chromium/Chrome is not on PATH.
No live AI/Bring service or production credentials are used. Screenshots are genuine renders.
"""

import json
import os
import shutil
import socket
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from uuid import uuid4

import uvicorn
from playwright.sync_api import expect, sync_playwright

import aircooker.app as application
from aircooker.models import Ingredient, Recipe

LIST_ID = "11111111-1111-4111-8111-111111111111"


class TestBring:
    """Only browser tests instantiate this connector; production uses the real adapter."""

    def __init__(self, root):
        self.capabilities = SimpleNamespace(uuid_create=False)
        self.runner = SimpleNamespace(close=lambda: None)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.runner.close()

    def lists(self):
        return [{"id": LIST_ID, "name": "Test list <safe>"}]


class TestAI:
    def extract_recipe(self, content):
        assert "Connection test soup" in content
        return Recipe(
            title="Synthetic probe",
            ingredients=[Ingredient(id=uuid4(), name="Carrots")],
            steps=["Simmer"],
        )

    def close(self):
        pass


def main():
    executable = (
        os.environ.get("CHROMIUM_EXECUTABLE")
        or shutil.which("chromium")
        or shutil.which("google-chrome")
    )
    if not executable:
        raise SystemExit("Chromium/Chrome is required for the browser smoke test")
    with TemporaryDirectory(prefix="aircooker-console-") as temporary:
        root = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        application.UnofficialBringConnector = TestBring
        application.provider_for = lambda config: TestAI()
        app = application.create_app(root, run_worker=False)
        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", access_log=False)
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        for _ in range(100):
            if server.started:
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("Browser-test server did not become ready")
        try:
            with sync_playwright() as browser_tool:
                browser = browser_tool.chromium.launch(
                    executable_path=executable, headless=True, args=["--no-sandbox"]
                )
                context = browser.new_context(
                    viewport={"width": 1200, "height": 900}, accept_downloads=True
                )
                page = context.new_page()

                # Chromium's localhost Secure-cookie handling differs from the separate
                # APIRequestContext jar. Read assertions through real in-page fetches.
                def get(path):
                    return page.evaluate("path => request(path)", path)

                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("dialog", lambda dialog: dialog.accept())
                page.goto(base)
                login = page.locator("#login")
                login.locator('[name="username"]').fill("cook")
                login.locator('[name="password"]').fill("synthetic browser household password")
                login.locator('[name="token"]').fill((root / "config/setup-token").read_text())
                login.locator('[name="name"]').fill("Browser kitchen")
                login.locator('[name="timezone"]').fill("Europe/Zurich")
                login.locator('button[type="submit"]').click()
                expect(page.locator("#dashboard")).to_be_visible(timeout=15000)
                expect(page.locator("#status")).to_have_text("Ready")
                page.get_by_text("Household settings", exact=True).click()
                household = page.locator("#household-form")
                household.locator('[name="name"]').fill("Test household <safe>")
                household.locator('[name="timezone"]').fill("Europe/Berlin")
                household.locator('button[type="submit"]').click()
                expect(page.locator("#status")).to_have_text("Changes saved.")
                assert get("/api/v1/household")["timezone"] == "Europe/Berlin"
                # Changing display language must not discard an unsaved form edit.
                household.locator('[name="name"]').fill("Unsaved household draft")
                page.locator("#language").select_option("de")
                expect(household.locator('[name="name"]')).to_have_value("Unsaved household draft")
                page.locator("#language").select_option("en")
                household.locator('[name="name"]').fill("Test household <safe>")
                page.get_by_text("Optional AI extraction", exact=True).click()
                ai = page.locator("#ai-form")
                ai.locator('[name="enabled"]').check()
                ai.locator('[name="provider"]').select_option("openai-compatible")
                ai.locator('[name="base_url"]').fill("https://ai.example/v1")
                ai.locator('[name="model"]').fill("synthetic-model")
                ai.locator('[name="api_key"]').fill("synthetic browser AI credential")
                ai.locator('button[type="submit"]').click()
                expect(page.locator("#status")).to_have_text("Changes saved.")
                expect(ai.locator('[name="api_key"]')).to_have_value("")
                assert "api_key" not in get("/api/v1/admin/ai")
                page.locator("#ai-test").click()
                expect(page.locator("#status")).to_have_text(
                    "The provider returned a validated recipe for the connection test."
                )
                page.get_by_text("Bring! connection", exact=True).click()
                bring = page.locator("#bring-form")
                bring.locator('[name="email"]').fill("cook@example.invalid")
                bring.locator('[name="password"]').fill("synthetic Bring browser password")
                bring.locator('button[type="submit"]').click()
                expect(page.locator("#status")).to_have_text(
                    "Credentials saved. Use Connect to verify access."
                )
                expect(bring.locator('[name="password"]')).to_have_value("")
                page.locator("#bring-test").click()
                expect(page.locator("#bring-list option")).to_have_text("Test list <safe>")
                page.locator("#bring-select").click()
                expect(page.locator("#status")).to_have_text(
                    "List selected. Automatic writes still require compatibility verification."
                )
                assert get("/api/v1/integrations/bring/status")["automatic_mutations"] is False
                assert page.locator("safe").count() == 0
                page.locator("#bring-retry").click()
                expect(page.locator("#status")).to_have_text(
                    "Reconciliation queued; external changes are pending."
                )
                page.get_by_text("Data export and import", exact=True).click()
                document = {
                    "format": "aircooker-household",
                    "version": 2,
                    "exported_at": datetime.now(UTC).isoformat(),
                    "household": {
                        "name": "Test household <safe>",
                        "timezone": "Europe/Berlin",
                        "language": "en",
                    },
                    "entities": [
                        {
                            "kind": "recipe",
                            "id": str(uuid4()),
                            "payload": {
                                "title": "Imported <safe> soup",
                                "servings": "2",
                                "steps": ["Simmer"],
                            },
                        }
                    ],
                    "media": [],
                }
                page.locator("#import-file").set_input_files(
                    {
                        "name": "household.json",
                        "mimeType": "application/json",
                        "buffer": json.dumps(document).encode(),
                    }
                )
                page.locator('#import-form button[type="submit"]').click()
                expect(page.locator("#status")).to_have_text("Household data imported.")
                assert get("/api/v1/admin/status")["recipes"] == 1
                with page.expect_download() as download:
                    page.locator("#export").click()
                archive = root / "export.zip"
                download.value.save_as(archive)
                assert archive.read_bytes().startswith(b"PK")
                page.locator("#import-file").set_input_files(str(archive))
                page.locator('#import-form button[type="submit"]').click()
                expect(page.locator("#status")).to_contain_text("duplicate_export_entity")
                assert get("/api/v1/admin/status")["recipes"] == 1
                # Revoke an independently authenticated synthetic device through the console.
                other_device = str(uuid4())
                other = page.request.post(
                    base + "/api/v1/auth/login",
                    data={
                        "username": "cook",
                        "password": "synthetic browser household password",
                        "device_id": other_device,
                    },
                ).json()
                page.locator("#reload").click()
                expect(page.locator("#status")).to_have_text("Ready")
                page.get_by_text("Account and devices", exact=True).click()
                row = page.locator(".session-row").filter(has_text=other_device[:8])
                row.get_by_role("button", name="Revoke session").click()
                expect(row).to_contain_text("Revoked")
                assert any(
                    s["id"] == other["session_id"] and s["revoked"]
                    for s in get("/api/v1/auth/sessions")
                )
                # Inspect desktop and German mobile in one bounded capture pass.
                screenshots = Path(os.environ.get("AIRCOOKER_SCREENSHOT_DIR", "docs/screenshots"))
                screenshots.mkdir(parents=True, exist_ok=True)
                page.locator("details").evaluate_all(
                    "elements => elements.forEach((element,index) => element.open=index===0)"
                )
                page.evaluate("scrollTo(0,0)")
                page.screenshot(path=str(screenshots / "admin-desktop.png"), full_page=True)
                page.locator("#language").select_option("de")
                page.set_viewport_size({"width": 390, "height": 844})
                page.locator("details").evaluate_all(
                    "elements => elements.forEach((element,index) => element.open=index===3)"
                )
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
                expect(page.locator(".metric span").first).to_have_text("Ausstehende Aufträge")
                expect(page.locator("#storage")).to_contain_text("Datenbank")
                page.evaluate("scrollTo(0,0)")
                page.screenshot(path=str(screenshots / "admin-mobile-de.png"), full_page=True)
                page.locator("#language").select_option("en")
                page.locator("details").evaluate_all(
                    "elements => elements.forEach((element,index) => element.open=index===2)"
                )
                ai.locator('[name="enabled"]').uncheck()
                ai.locator('button[type="submit"]').click()
                expect(page.locator("#status")).to_have_text("Changes saved.")
                assert get("/api/v1/admin/ai")["enabled"] is False
                page.locator("details").evaluate_all(
                    "elements => elements.forEach((element,index) => element.open=index===1)"
                )
                password = page.locator("#password-form")
                password.locator('[name="current_password"]').fill(
                    "synthetic browser household password"
                )
                password.locator('[name="new_password"]').fill(
                    "replacement synthetic browser password"
                )
                password.locator('button[type="submit"]').click()
                expect(page.locator("#authentication")).to_be_visible()
                assert (
                    page.evaluate(
                        "async () => (await fetch('/api/v1/auth/sessions', {credentials:'same-origin'})).status"
                    )
                    == 401
                )
                assert not errors, errors
                browser.close()
                print(
                    "PASS: Chromium console setup, CSRF cookies, household editing, AI settings/probe, Bring list setup/retry, JSON/ZIP import/export, session revocation, password change and EN/DE mobile layout. AI/Bring adapters are test-only doubles."
                )
        finally:
            server.should_exit = True
            thread.join(timeout=5)


if __name__ == "__main__":
    main()
