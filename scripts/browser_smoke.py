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
from aircooker.jobs import enqueue
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
                expect(page).to_have_title("mealf · household console")
                expect(page.get_by_role("link", name="mealf", exact=True)).to_be_visible()
                page.wait_for_function(
                    "[...document.querySelectorAll('.wordmark img')].every(image=>image.complete&&image.naturalWidth>0)"
                )
                login = page.locator("#login")
                expect(login.locator('[name="username"]')).to_be_visible()
                screenshots = Path(os.environ.get("AIRCOOKER_SCREENSHOT_DIR", "docs/screenshots"))
                screenshots.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshots / "admin-setup.png"), full_page=True)
                login.locator('[name="username"]').fill("cook")
                login.locator('[name="password"]').fill("synthetic browser household password")
                login.locator('[name="token"]').fill((root / "config/setup-token").read_text())
                login.locator('[name="name"]').fill("Browser kitchen")
                login.locator('[name="timezone"]').fill("Europe/Zurich")
                login.locator('button[type="submit"]').click()
                expect(page.locator("#dashboard")).to_be_visible(timeout=15000)
                expect(page.locator("#status")).to_have_text("Ready")
                expect(page.locator("#recent-imports")).to_have_text("No recipe imports yet.")
                private_marker = "private_import_content_do_not_display"
                with app.state.database.transaction() as db:
                    enqueue(db, "recipe.import", "diagnostics-browser", {"text": private_marker})
                    db.execute(
                        "UPDATE background_job SET state='failed',error_code=? WHERE dedupe_key=?",
                        (private_marker, "diagnostics-browser"),
                    )
                    db.execute(
                        "INSERT INTO import_draft(id,source_url,source_platform,state,recipe,warnings,error_code,confirmed_recipe_id,created_at) VALUES (?,?,?,'needs_input',NULL,'[]',?,NULL,?)",
                        (
                            str(uuid4()),
                            "https://private.example",
                            "website",
                            private_marker,
                            time.time(),
                        ),
                    )
                page.locator("#reload").click()
                expect(page.locator("#recent-imports .job")).to_contain_text("Needs your input")
                expect(page.locator("#queue-counts")).to_contain_text("Failed: 1")
                assert private_marker not in page.locator("body").inner_text()
                assert "private.example" not in page.locator("body").inner_text()
                page.locator("#language").select_option("de")
                expect(page.locator("#recent-imports .job")).to_contain_text(
                    "Deine Eingabe wird benötigt"
                )
                expect(page.locator("#queue-counts")).to_contain_text("Fehlgeschlagen: 1")
                page.locator("#language").select_option("en")
                page.locator('[data-page-link="household"]').click()
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
                page.locator('[data-page-link="ai"]').click()
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
                page.locator('[data-page-link="bring"]').click()
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
                page.locator('[data-page-link="data"]').click()
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
                page.locator('[data-page-link="overview"]').click()
                page.locator("#reload").click()
                expect(page.locator("#status")).to_have_text("Ready")
                page.locator('[data-page-link="security"]').click()
                row = page.locator(".session-row").filter(has_text=other_device[:8])
                row.get_by_role("button", name="Revoke session").click()
                expect(row).to_contain_text("Revoked")
                assert any(
                    s["id"] == other["session_id"] and s["revoked"]
                    for s in get("/api/v1/auth/sessions")
                )
                # One batched capture pass: real UI, synthetic household, EN/DE and themes.
                screenshots = Path(os.environ.get("AIRCOOKER_SCREENSHOT_DIR", "docs/screenshots"))
                screenshots.mkdir(parents=True, exist_ok=True)
                page.locator('[data-page-link="overview"]').click()
                page.screenshot(path=str(screenshots / "admin-desktop.png"), full_page=True)
                page.emulate_media(color_scheme="dark")
                page.screenshot(path=str(screenshots / "admin-desktop-dark.png"), full_page=True)
                page.emulate_media(color_scheme="light")
                page.locator("#language").select_option("de")
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1")
                expect(page.locator(".metric span").first).to_have_text("Ausstehende Aufträge")
                expect(page.locator("#storage")).to_contain_text("Datenbank")
                page.screenshot(path=str(screenshots / "admin-mobile-de.png"), full_page=True)
                page.locator('[data-page-link="ai"]').click()
                page.screenshot(path=str(screenshots / "admin-mobile-ai-de.png"), full_page=True)
                # Text zoom and narrow screens must keep settings usable.
                page.set_viewport_size({"width": 320, "height": 844})
                page.route(
                    "**/text-zoom-test.css",
                    lambda route: route.fulfill(
                        content_type="text/css", body="html { font-size: 200% !important; }"
                    ),
                )
                zoom = page.add_style_tag(url=base + "/text-zoom-test.css")
                for key in ["overview", "household", "ai", "bring", "security", "data"]:
                    page.locator(f'[data-page-link="{key}"]').click()
                    assert page.locator('[data-page-link][aria-current="page"]').count() == 1
                    assert page.locator("[data-page]:visible").count() == 1
                    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), (
                        key,
                        page.evaluate("""() => [...document.querySelectorAll('body *')]
                          .filter(e => e.getBoundingClientRect().right > innerWidth + 1)
                          .map(e => [e.tagName, e.id, Math.round(e.getBoundingClientRect().width)])
                          .slice(0, 12)"""),
                    )
                zoom.evaluate("element => element.remove()")
                page.set_viewport_size({"width": 390, "height": 844})
                page.locator('[data-page-link="household"]').click()
                expect(household.locator('[name="name"]')).to_have_value("Test household <safe>")
                page.screenshot(
                    path=str(screenshots / "admin-mobile-settings-de.png"), full_page=True
                )
                # Navigation and language changes preserve unsaved settings, with no overflow.
                household.locator('[name="name"]').fill("Unstored navigation draft")
                page.locator('[data-page-link="ai"]').click()
                page.locator('[data-page-link="household"]').click()
                expect(household.locator('[name="name"]')).to_have_value(
                    "Unstored navigation draft"
                )
                page.locator("#language").select_option("en")
                page.locator('[data-page-link="ai"]').click()
                ai.locator('[name="enabled"]').uncheck()
                ai.locator('button[type="submit"]').click()
                expect(page.locator("#status")).to_have_text("Changes saved.")
                assert get("/api/v1/admin/ai")["enabled"] is False
                page.locator('[data-page-link="security"]').click()
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
