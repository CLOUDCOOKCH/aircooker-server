"""Whole-PWA task-flow regression on a real disposable household; no external services."""

import json
import os
import shutil
import socket
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
import uvicorn
from browser_navigation import navigate
from browser_settings import settings_section
from playwright.sync_api import expect, sync_playwright

from mealf.app import create_app


def main():
    captures = Path(os.environ.get("MEALF_UX_SCREENSHOT_DIR", "build/pwa-ux-browser"))
    capture = os.environ.get("MEALF_CAPTURE") == "1"
    captures.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="mealf-ux-") as directory:
        root = Path(directory)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        os.environ["LOG_SETUP_TOKEN"] = "false"
        server = uvicorn.Server(
            uvicorn.Config(
                create_app(root, run_worker=False),
                host="127.0.0.1",
                port=port,
                log_level="error",
                access_log=False,
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
            with httpx.Client(base_url=base, trust_env=False, timeout=20) as operator:
                device = str(uuid4())
                setup = operator.post(
                    "/api/v1/setup",
                    headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
                    json={
                        "name": "Synthetic UX kitchen",
                        "username": "cook",
                        "password": "synthetic UX kitchen password",
                        "timezone": "Europe/Zurich",
                        "device_id": device,
                    },
                )
                assert setup.status_code == 201
                operator.headers["Authorization"] = "Bearer " + setup.json()["access_token"]
                image_id = str(uuid4())
                uploaded = operator.put(
                    "/api/v1/media/" + image_id,
                    files={
                        "file": (
                            "illustrative-demo-chicken.png",
                            Path("frontend/public/art/lemon-chicken.png").read_bytes(),
                            "image/png",
                        )
                    },
                )
                assert uploaded.status_code == 200, uploaded.status_code
                day = str(datetime.now(ZoneInfo("Europe/Zurich")).date())
                recipe_ids = [str(uuid4()) for _ in range(3)]
                mutations = []

                def add(kind, value, eid=None):
                    mid = str(uuid4())
                    mutations.append(
                        {
                            "mutation_id": mid,
                            "idempotency_key": mid,
                            "entity_id": eid or str(uuid4()),
                            "kind": kind,
                            "operation": "upsert",
                            "base_revision": 0,
                            "device_id": device,
                            "client_timestamp": "2000-01-01T00:00:00Z",
                            "payload": value,
                        }
                    )

                for i, title in enumerate(
                    ["Lemon & herb chicken", "Creamy tomato pasta", "Overnight oats"]
                ):
                    add(
                        "recipe",
                        {
                            "title": title,
                            "description": "Synthetic household recipe for UI verification.",
                            "servings": "2",
                            "rating": 5 - i,
                            "image_id": image_id if i == 0 else None,
                            "ingredients": [
                                {
                                    "id": str(uuid4()),
                                    "name": "Rice" if i == 0 else "Tomatoes",
                                    "quantity": "200",
                                    "unit": "g",
                                }
                            ],
                            "steps": ["Cook the ingredients until ready.", "Serve and enjoy."],
                            "provenance": {
                                "content": "Synthetic UI fixture",
                                "image": "Existing original AI-generated demo illustration; not actual cooking photography",
                            },
                        },
                        recipe_ids[i],
                    )
                for category, rid in zip(
                    ["breakfast", "lunch", "dinner"], recipe_ids[::-1], strict=True
                ):
                    add(
                        "meal",
                        {"recipe_id": rid, "date": day, "category": category, "servings": "2"},
                    )
                add("pantry", {"name": "Olive oil", "available": True})
                leftover_id = str(uuid4())
                add(
                    "leftover",
                    {"recipe_id": recipe_ids[2], "portions": "1", "produced_on": day},
                    leftover_id,
                )
                assert (
                    operator.post("/api/v1/sync/push", json={"mutations": mutations}).status_code
                    == 200
                )
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
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.goto(base + "/app/")
                    page.get_by_role("button", name="Open your kitchen", exact=True).click()
                    page.get_by_label("Username", exact=True).fill("cook")
                    page.get_by_label("Password", exact=True).fill("synthetic UX kitchen password")
                    page.get_by_role("button", name="Sign in", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text(
                        "Up to date", timeout=20000
                    )

                    def nav(label):
                        navigate(page, label)

                    def shot(name):
                        if capture:
                            expect(page.locator(".toast")).not_to_be_visible()
                            page.evaluate("scrollTo(0,0)")
                            page.mouse.move(0, 0)
                            page.screenshot(
                                path=str(captures / (name + ".png")),
                                full_page=page.locator(".sheet[open]").count() == 0,
                                animations="disabled",
                            )

                    def audit():
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= innerWidth"
                        ), page.url
                        if page.viewport_size["width"] <= 800:
                            assert page.locator(".connection-bar").evaluate("""bar=>{
                                const status=bar.querySelector('.connection-status').getBoundingClientRect();
                                const account=bar.querySelector('.account-button').getBoundingClientRect();
                                return status.top>=account.bottom && status.right<=innerWidth;
                            }"""), "Phone sync status must have its own row"
                        page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                        violations = page.evaluate(
                            "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))"
                        )
                        assert not violations, violations

                    expect(
                        page.get_by_role("button", name="Plan a meal", exact=True)
                    ).to_be_visible()
                    expect(
                        page.get_by_role("heading", name="Today’s meals", exact=True)
                    ).to_be_visible()
                    audit()
                    shot("home-desktop")
                    nav("Calendar")
                    audit()
                    shot("calendar-desktop")
                    assert page.locator(".nav-links > button").all_text_contents() == [
                        "Today",
                        "Plan",
                        "Recipes",
                        "Shopping",
                    ]
                    nav("Settings")
                    page.get_by_role("button", name="Back", exact=True).click()
                    expect(page.locator(".calendar-view-switch")).to_be_visible()
                    nav("Pantry")
                    expect(
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Shopping list", exact=True
                        )
                    ).to_have_attribute("aria-current", "page")
                    page.get_by_role("button", name="Back", exact=True).click()
                    expect(page.locator(".shopping-page")).to_be_visible()
                    nav("Calendar")
                    page.get_by_role("button", name="Next week", exact=True).click()
                    slot = page.locator('.calendar-slot[data-category="breakfast"]').first
                    quick_day = slot.get_attribute("data-date")
                    slot.locator(".calendar-add").click()
                    picker = page.get_by_role("dialog", name="Plan a meal", exact=True)
                    expect(picker.locator(".meal-choice")).to_have_count(3)
                    picker.get_by_label("Search recipes", exact=True).fill("no such dish")
                    expect(picker.get_by_role("status")).to_have_text(
                        "No matching recipes. Try another name."
                    )
                    picker.get_by_label("Search recipes", exact=True).fill("pasta")
                    expect(picker.locator(".meal-choice")).to_have_count(1)
                    picker.get_by_role("button", name="Meal options · Creamy tomato pasta").click()
                    expect(picker.get_by_label("Servings", exact=True)).to_have_value("2")
                    audit()
                    shot("meal-options-desktop")
                    picker.get_by_role("button", name="Choose another recipe", exact=True).click()
                    expect(picker.get_by_label("Search recipes", exact=True)).to_have_value("pasta")
                    audit()
                    shot("meal-picker-desktop")
                    # Real offline local transaction; double activation must queue only one meal.
                    page.wait_for_function("!!navigator.serviceWorker.controller")
                    context.set_offline(True)
                    picker.get_by_role(
                        "button", name="Add · Creamy tomato pasta", exact=True
                    ).evaluate("button=>{button.click();button.click()}")
                    expect(picker).not_to_be_visible()
                    expect(slot.locator(".meal-row")).to_have_count(1)
                    page.reload()
                    nav("Calendar")
                    page.get_by_role("button", name="Next week", exact=True).click()
                    slot = page.locator(
                        f'.calendar-slot[data-date="{quick_day}"][data-category="breakfast"]'
                    )
                    expect(slot.locator(".meal-row")).to_have_count(1)
                    expect(slot.locator(".meal-open")).to_contain_text("Creamy tomato pasta")
                    context.set_offline(False)
                    page.get_by_role("button", name="Sync now", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text(
                        "Up to date", timeout=20000
                    )
                    server_meals = operator.get("/api/v1/calendar/meals").json()["items"]
                    added = [row for row in server_meals if row["payload"]["date"] == quick_day]
                    assert len(added) == 1 and added[0]["payload"]["servings"] == "2"
                    assert added[0]["payload"]["recipe_id"] == recipe_ids[1]
                    # Full options remain available and save exact date/portions/recurrence.
                    page.locator(
                        '.calendar-slot[data-category="lunch"] .calendar-add'
                    ).first.click()
                    picker.get_by_role("button", name="Meal options · Lemon & herb chicken").click()
                    picker.get_by_label("Servings", exact=True).fill("3")
                    picker.get_by_label("Repeat every").select_option("1")
                    until_day = str(date.fromisoformat(quick_day) + timedelta(days=14))
                    picker.get_by_label("Until", exact=True).fill(until_day)
                    picker.get_by_role("button", name="Save", exact=True).click()
                    expect(picker).not_to_be_visible()
                    expect(
                        page.locator('.calendar-slot[data-category="lunch"] .meal-open')
                    ).to_contain_text("3 servings")
                    page.get_by_role("button", name="Sync now", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text(
                        "Up to date", timeout=20000
                    )
                    rows = operator.get("/api/v1/calendar/meals").json()["items"]
                    recurring = [r["payload"] for r in rows if r["payload"].get("recurrence")]
                    assert len(rows) == 5 and len(recurring) == 1
                    assert (
                        recurring[0]["recipe_id"] == recipe_ids[0]
                        and recurring[0]["servings"] == "3"
                    )
                    assert recurring[0]["recurrence"] == {
                        "interval_weeks": 1,
                        "until": until_day,
                        "exceptions": [],
                    }
                    page.locator(
                        '.calendar-slot[data-category="dinner"] .calendar-add'
                    ).first.click()
                    picker.locator(".meal-leftover-choice").click()
                    expect(picker).not_to_be_visible()
                    expect(
                        page.locator('.calendar-slot[data-category="dinner"] .meal-open')
                    ).to_contain_text("1 serving")
                    page.get_by_role("button", name="Sync now", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text(
                        "Up to date", timeout=20000
                    )
                    rows = operator.get("/api/v1/calendar/meals").json()["items"]
                    leftovers_planned = [
                        r["payload"] for r in rows if r["payload"].get("leftover_id")
                    ]
                    assert len(rows) == 6 and len(leftovers_planned) == 1
                    assert leftovers_planned[0]["leftover_id"] == leftover_id
                    assert (
                        leftovers_planned[0]["servings"] == "1"
                        and leftovers_planned[0]["recurrence"] is None
                    )
                    page.get_by_role("button", name="Today", exact=True).last.click()
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.locator(".calendar-slot .slot-heading button").first.click()
                    audit()
                    shot("meal-picker-phone-flo")
                    picker.get_by_role("button", name="Close", exact=True).click()
                    page.set_viewport_size({"width": 1440, "height": 1000})
                    nav("Settings")
                    expect(page.locator(".settings-disclosure[open]")).to_have_count(0)
                    expect(page.get_by_label("Language", exact=True)).not_to_be_visible()
                    audit()
                    shot("settings-desktop")
                    settings_section(page, "Your household")
                    page.get_by_label("Language", exact=True).select_option("de")
                    settings_section(page, "Design-Bibliothek")
                    page.get_by_role("radio", name="After Dark", exact=True).check()
                    page.set_viewport_size({"width": 390, "height": 844})
                    for label, name in [
                        ("Start", "home"),
                        ("Kalender", "calendar"),
                        ("Rezepte", "recipes"),
                        ("Vorrat", "pantry"),
                        ("Einkaufsliste", "shopping"),
                        ("Einstellungen", "settings"),
                    ]:
                        nav(label)
                        if name == "shopping":
                            expect(
                                page.get_by_role(
                                    "button", name="Mit Bring! synchronisieren", exact=True
                                )
                            ).to_be_disabled()
                            expect(
                                page.get_by_text("Auf deinem Server eingereiht.", exact=False)
                            ).not_to_be_visible()
                            expect(page.locator('a.primary[href="/admin/#bring"]')).to_be_visible()
                        audit()
                        shot(name + "-phone-de-dark")
                        if name == "calendar":
                            page.locator(".calendar-slot .slot-heading button").first.click()
                            audit()
                            shot("meal-picker-phone-de-dark")
                            page.get_by_role("button", name="Schließen", exact=True).click()
                    settings_section(page, "Dieses Gerät")
                    page.get_by_role("button", name="Synchronisierung prüfen", exact=True).click()
                    expect(page.locator(".sync-report")).to_be_visible()
                    report = json.loads(page.locator(".sync-report").input_value())
                    assert report["local"]["records"]["recipe"] == 3
                    settings_section(page, "Dein Haushalt")
                    page.get_by_label("Sprache", exact=True).select_option("en")
                    nav("Recipes")
                    page.get_by_label("Search recipes", exact=True).fill("pasta")
                    expect(page.locator(".recipe-card")).to_have_count(1)
                    page.get_by_role("button", name="Clear search", exact=True).click()
                    page.get_by_label("Sort recipes", exact=True).select_option("rating")
                    expect(page.locator(".recipe-card").first).to_contain_text(
                        "Lemon & herb chicken"
                    )
                    page.locator(".recipe-card").first.click()
                    audit()
                    shot("recipe-detail-phone")
                    page.get_by_role("link", name="Method", exact=True).click()
                    expect(page.locator("#recipe-instructions")).to_be_in_viewport()
                    nav("Recipes")
                    page.get_by_role("button", name="Import recipe", exact=True).first.click()
                    expect(page.get_by_label("Recipe text", exact=True)).not_to_be_visible()
                    page.locator(".import-alternative > summary").click()
                    expect(page.get_by_label("Recipe text", exact=True)).to_be_visible()
                    page.locator(".import-alternative > summary").click()
                    audit()
                    shot("import-phone")
                    nav("Recipes")
                    page.get_by_role("button", name="New recipe", exact=True).click()
                    expect(page.get_by_label("Recipe name", exact=True)).to_be_visible()
                    expect(
                        page.get_by_label("Preparation time (minutes)", exact=True)
                    ).not_to_be_visible()
                    page.get_by_label("Recipe name", exact=True).fill("Offline UX rice")
                    page.get_by_role("button", name="Add ingredient", exact=True).click()
                    page.get_by_label("Ingredient 1", exact=True).fill("Rice")
                    page.get_by_label("Quantity", exact=True).fill("200")
                    page.get_by_label("Unit", exact=True).fill("g")
                    page.get_by_role("button", name="Add step", exact=True).click()
                    page.get_by_label("Step 1", exact=True).fill("Cook the rice.")
                    page.locator(".editor-optional > summary").click()
                    page.get_by_label("Preparation time (minutes)", exact=True).fill("10")
                    page.locator(".editor-optional > summary").click()
                    audit()
                    shot("recipe-editor-phone")
                    page.wait_for_function("!!navigator.serviceWorker.controller")
                    context.set_offline(True)
                    page.get_by_role("button", name="Save", exact=True).click()
                    expect(
                        page.locator(".recipe-card").filter(has_text="Offline UX rice")
                    ).to_be_visible()
                    page.reload()
                    nav("Recipes")
                    expect(
                        page.locator(".recipe-card").filter(has_text="Offline UX rice")
                    ).to_be_visible()
                    context.set_offline(False)
                    page.get_by_role("button", name="Sync now", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text(
                        "Up to date", timeout=20000
                    )
                    saved = operator.get("/api/v1/recipes").json()["items"]
                    assert (
                        len(saved) == 4
                        and next(r for r in saved if r["payload"]["title"] == "Offline UX rice")[
                            "payload"
                        ]["times"]["prep_minutes"]
                        == 10
                    )
                    nav("Settings")
                    settings_section(page, "Your household")
                    page.get_by_label("Language", exact=True).select_option("de")
                    page.set_viewport_size({"width": 320, "height": 740})
                    nav("Kalender")
                    page.get_by_role("button", name="3 Tage", exact=True).click()
                    expect(page.locator(".calendar-week")).to_have_attribute("data-view", "three")
                    assert page.locator(".calendar-week").evaluate("e=>e.scrollWidth>e.clientWidth")
                    audit()
                    shot("calendar-phone-320-de-dark")
                    nav("Einstellungen")
                    audit()
                    shot("settings-phone-320-de-dark")
                    settings_section(page, "Design-Bibliothek")
                    page.get_by_role("radio", name="Sunday", exact=True).check()
                    nav("Start")
                    audit()
                    shot("home-phone-320-sunday")
                    nav("Kalender")
                    page.locator(".calendar-slot .slot-heading button").first.click()
                    audit()
                    shot("meal-picker-phone-320-sunday")
                    page.locator(".meal-choice > .icon-button").first.click()
                    audit()
                    shot("meal-options-phone-320-sunday")
                    page.get_by_role("button", name="Schließen", exact=True).click()
                    assert page.locator(".nav-links > button").evaluate_all(
                        "b=>b.length===4&&b.every(e=>{let r=e.getBoundingClientRect();return r.width>=44&&r.height>=44&&r.right<=innerWidth&&r.left>=0})"
                    )
                    # Explicit UI-response fixture: ready/queued must still show progress.
                    queued_snapshot = operator.get("/api/v1/planning/shopping").json()
                    assert queued_snapshot["connection_state"] == "not_configured"
                    queued_snapshot.update(
                        connection_state="ready", job_state="queued", error_code=None
                    )
                    page.route(
                        "**/api/v1/planning/shopping",
                        lambda route: route.fulfill(json=queued_snapshot),
                    )
                    nav("Einkaufsliste")
                    expect(
                        page.get_by_role("button", name="Wird abgeglichen…", exact=True)
                    ).to_be_disabled()
                    expect(
                        page.get_by_text("Auf deinem Server eingereiht.", exact=False)
                    ).to_be_visible()
                    page.unroute("**/api/v1/planning/shopping")
                    assert not errors, errors
                    browser.close()
            print(
                "PASS: real household, four primary destinations with account/pantry return routes, searchable quick planning, one offline meal after double activation/reload/sync, custom portions/recurrence, collapsed Settings, EN/DE three themes, recipe anchors, offline recipe Save/reload/sync and 320px scrollable calendar; Axe on desktop/390/320. No live services or physical iPhone."
            )
        finally:
            server.should_exit = True
            thread.join(timeout=10)


if __name__ == "__main__":
    main()
