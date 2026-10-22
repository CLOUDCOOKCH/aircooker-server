"""Real household/two-device sync; explicitly injected stale-page and HTTP fault responses."""

import json
import os
import shutil
import socket
import threading
import time
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
import uvicorn
from playwright.sync_api import expect, sync_playwright

from mealf.app import create_app


def main():
    captures = Path(os.environ.get("MEALF_SYNC_SCREENSHOT_DIR", "build/sync-status-browser"))
    captures.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="mealf-sync-status-") as directory:
        root = Path(directory)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        os.environ["LOG_SETUP_TOKEN"] = "false"
        app = create_app(root, run_worker=False)
        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", access_log=False)
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        try:
            for _ in range(100):
                if server.started:
                    break
                time.sleep(0.05)
            assert server.started
            with httpx.Client(base_url=base, trust_env=False) as operator:
                device = str(uuid4())
                response = operator.post(
                    "/api/v1/setup",
                    headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
                    json={
                        "name": "Synthetic sync kitchen",
                        "username": "cook",
                        "password": "synthetic sync password",
                        "timezone": "Europe/Zurich",
                        "device_id": device,
                    },
                )
                assert response.status_code == 201
                operator.headers["Authorization"] = "Bearer " + response.json()["access_token"]
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        executable_path=shutil.which("chromium") or shutil.which("google-chrome"),
                        args=["--no-sandbox"],
                    )
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 1000},
                        permissions=["clipboard-read", "clipboard-write"],
                    )
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))

                    def login(screen):
                        screen.goto(base + "/app/")
                        screen.get_by_role("button", name="Open your kitchen", exact=True).click()
                        screen.get_by_label("Username", exact=True).fill("cook")
                        screen.get_by_label("Password", exact=True).fill("synthetic sync password")
                        screen.get_by_role("button", name="Sign in", exact=True).click()
                        expect(screen.locator(".connection-status")).to_have_text(
                            "Up to date", timeout=20000
                        )

                    def nav(screen, name):
                        screen.get_by_role("navigation").get_by_role(
                            "button", name=name, exact=True
                        ).click()

                    def audit(screen):
                        assert screen.locator(".sync-report + .form-actions > button").evaluate_all(
                            "buttons => buttons.length === 2 && buttons.every(button => button.getBoundingClientRect().height >= 44)"
                        )
                        screen.evaluate(
                            Path("frontend/node_modules/axe-core/axe.min.js").read_text()
                        )
                        assert not screen.evaluate(
                            "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                        )

                    login(page)
                    session = page.evaluate(
                        "async()=> (await fetch('/api/v1/pwa/auth/session')).json()"
                    )
                    initial = operator.get("/api/v1/sync/state").json()
                    rid = str(uuid4())

                    def mutation(kind, payload, eid=None):
                        mid = str(uuid4())
                        return {
                            "mutation_id": mid,
                            "idempotency_key": mid,
                            "entity_id": eid or str(uuid4()),
                            "kind": kind,
                            "operation": "upsert",
                            "payload": payload,
                            "device_id": device,
                            "base_revision": 0,
                            "client_timestamp": "2000-01-01T00:00:00Z",
                        }

                    planned_date = str(datetime.now(ZoneInfo("Europe/Zurich")).date())
                    created = operator.post(
                        "/api/v1/sync/push",
                        json={
                            "mutations": [
                                mutation(
                                    "recipe",
                                    {
                                        "title": "Server sync soup",
                                        "servings": "2",
                                        "ingredients": [],
                                        "steps": ["Cook soup."],
                                    },
                                    rid,
                                ),
                                mutation(
                                    "meal",
                                    {
                                        "recipe_id": rid,
                                        "date": planned_date,
                                        "category": "dinner",
                                        "servings": "2",
                                    },
                                ),
                                mutation("pantry", {"name": "Rice", "available": True}),
                            ]
                        },
                    )
                    assert created.status_code == 200, created.text
                    # Reproduce a stale cache returning an old empty page after a fresh head.
                    pattern = "**/api/v1/sync/pull?*"
                    page.route(
                        pattern,
                        lambda route: route.fulfill(
                            json={
                                "changes": [],
                                "cursor": initial["cursor"],
                                "cursor_token": initial["token"],
                                "has_more": False,
                            }
                        ),
                    )
                    page.get_by_role("button", name="Sync now", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text("Sync failed")
                    expect(page.get_by_role("alert")).to_contain_text(
                        "Some server changes have not arrived"
                    )
                    nav(page, "Settings")
                    page.get_by_role("button", name="Check sync connection", exact=True).click()
                    report = page.get_by_label("Sync report", exact=True)
                    expect(report).to_be_visible()
                    assert '"sync_incomplete"' in report.input_value()
                    data = json.loads(report.input_value())
                    assert data["local"]["cursor"] == 0 and data["history"]["cursor"] == 3
                    assert (
                        data["storage"]["server_recipes"] == 1
                        and data["local"]["records"]["recipe"] == 0
                    )
                    assert (
                        data["history"]["local_proof_matches"] and data["session"]["device_matches"]
                    )
                    for secret in [
                        rid,
                        device,
                        session["session_id"],
                        initial["token"],
                        "Server sync soup",
                        "synthetic sync password",
                    ]:
                        # 'root' is a generic English word; the history token must not be a field.
                        if secret != "root":
                            assert secret not in report.input_value()
                    assert '"token"' not in report.input_value()
                    page.get_by_role("button", name="Copy report", exact=True).click()
                    expect(
                        page.get_by_role("button", name="Report copied", exact=True)
                    ).to_be_visible()
                    assert page.evaluate("navigator.clipboard.readText()") == report.input_value()
                    audit(page)
                    page.screenshot(path=str(captures / "sync-report-desktop.png"), full_page=True)
                    report.scroll_into_view_if_needed()
                    page.screenshot(path=str(captures / "sync-report-detail-desktop.png"))
                    page.unroute(pattern)
                    page.get_by_role("button", name="Sync now", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text("Up to date")
                    nav(page, "Recipes")
                    expect(
                        page.locator(".recipe-card").filter(has_text="Server sync soup")
                    ).to_be_visible()
                    nav(page, "Calendar")
                    expect(
                        page.locator(".meal-open").filter(has_text="Server sync soup")
                    ).to_be_visible()
                    nav(page, "Pantry")
                    expect(page.get_by_text("Rice", exact=True)).to_be_visible()
                    other = browser.new_context(viewport={"width": 390, "height": 844})
                    second = other.new_page()
                    second.on("pageerror", lambda error: errors.append(str(error)))
                    login(second)
                    nav(second, "Recipes")
                    second.locator(".recipe-card").filter(has_text="Server sync soup").click()
                    second.get_by_role("button", name="Edit", exact=True).click()
                    second.get_by_label("Recipe name", exact=True).fill("Offline device soup")
                    second.wait_for_function("!!navigator.serviceWorker.controller")
                    other.set_offline(True)
                    second.get_by_role("button", name="Save", exact=True).click()
                    expect(
                        second.locator(".recipe-card").filter(has_text="Offline device soup")
                    ).to_be_visible()
                    second.reload()
                    nav(second, "Recipes")
                    expect(
                        second.locator(".recipe-card").filter(has_text="Offline device soup")
                    ).to_be_visible()
                    other.set_offline(False)
                    second.get_by_role("button", name="Sync now", exact=True).click()
                    expect(second.locator(".connection-status")).to_have_text("Up to date")
                    page.get_by_role("button", name="Sync now", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text("Up to date")
                    nav(page, "Recipes")
                    expect(
                        page.locator(".recipe-card").filter(has_text="Offline device soup")
                    ).to_be_visible()
                    assert (
                        operator.get("/api/v1/recipes/" + rid).json()["payload"]["title"]
                        == "Offline device soup"
                    )
                    with app.state.database.transaction() as db:
                        db.execute(
                            "UPDATE session SET access_expires=0 WHERE id=?",
                            (session["session_id"],),
                        )
                    page.get_by_role("button", name="Sync now", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text("Up to date")
                    nav(page, "Settings")
                    page.get_by_label("Language", exact=True).select_option("de")
                    page.evaluate("window.mealfAppearance.set('after-dark')")
                    page.set_viewport_size({"width": 390, "height": 844})
                    # Fail while there is no outbox: the former header incorrectly said synced.
                    state_pattern = "**/api/v1/sync/state?*"
                    page.route(
                        state_pattern,
                        lambda route: route.fulfill(
                            status=503, json={"error": {"code": "storage_unavailable"}}
                        ),
                    )
                    page.get_by_role("button", name="Jetzt synchronisieren", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text(
                        "Abgleich fehlgeschlagen"
                    )
                    page.get_by_role("button", name="Synchronisierung prüfen", exact=True).click()
                    report = page.get_by_label("Synchronisierungsbericht", exact=True)
                    expect(report).to_be_visible()
                    assert '"storage_unavailable"' in report.input_value()
                    assert json.loads(report.input_value())["history"]["ok"] is False
                    report.evaluate("element=>{element.focus();element.select()}")
                    assert report.evaluate("element=>element.selectionEnd>element.selectionStart")
                    audit(page)
                    page.screenshot(
                        path=str(captures / "sync-report-phone-de-dark.png"), full_page=True
                    )
                    report.scroll_into_view_if_needed()
                    page.screenshot(path=str(captures / "sync-report-detail-phone-de-dark.png"))
                    page.set_viewport_size({"width": 320, "height": 740})
                    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                    page.screenshot(
                        path=str(captures / "sync-report-phone-320-de-dark.png"), full_page=True
                    )
                    report.scroll_into_view_if_needed()
                    page.screenshot(path=str(captures / "sync-report-detail-phone-320-de-dark.png"))
                    page.unroute(state_pattern)
                    page.get_by_role("button", name="Jetzt synchronisieren", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text("Aktuell")
                    assert not errors, errors
                    browser.close()
            print(
                "PASS: real two-device recipe/calendar/pantry sync, offline Save/reload/reconnect, expired-session refresh, stale-page rejection, no-outbox failure status, redacted copyable diagnostics, desktop/DE390 Axe and320 layout; stale-page/503 responses are explicit test faults, not a diagnosis of the user deployment."
            )
        finally:
            server.should_exit = True
            thread.join(timeout=10)


if __name__ == "__main__":
    main()
