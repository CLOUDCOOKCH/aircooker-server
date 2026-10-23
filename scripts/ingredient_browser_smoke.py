"""Real household ingredient choices, compact pantry and durable offline edits."""

import json
import os
import shutil
import socket
import ssl
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import httpx
import uvicorn
from browser_navigation import navigate
from browser_settings import settings_section
from playwright.sync_api import expect, sync_playwright

from mealf.app import create_app


def main():
    captures = Path(os.environ.get("MEALF_INGREDIENT_SCREENSHOT_DIR", "build/ingredient-browser"))
    captures.mkdir(parents=True, exist_ok=True)
    capture = os.environ.get("MEALF_CAPTURE") == "1"
    engine = os.environ.get("MEALF_LAYOUT_ENGINE", "chromium")
    assert engine in {"chromium", "webkit"}
    tls_root = os.environ.get("MEALF_BROWSER_TEST_TLS")
    if engine == "webkit" and not tls_root:
        raise ValueError("WebKit authentication requires trusted loopback HTTPS fixtures")
    with TemporaryDirectory(prefix="mealf-ingredients-") as directory:
        root = Path(directory)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"{'https' if tls_root else 'http'}://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        os.environ["LOG_SETUP_TOKEN"] = "false"
        server = uvicorn.Server(
            uvicorn.Config(
                create_app(root, run_worker=False),
                host="127.0.0.1",
                port=port,
                log_level="error",
                access_log=False,
                ssl_certfile=str(Path(tls_root) / "server.crt") if tls_root else None,
                ssl_keyfile=str(Path(tls_root) / "server.key") if tls_root else None,
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
            trust = (
                ssl.create_default_context(cafile=str(Path(tls_root) / "ca.crt"))
                if tls_root
                else True
            )
            with httpx.Client(base_url=base, trust_env=False, verify=trust) as operator:
                device = str(uuid4())
                setup = operator.post(
                    "/api/v1/setup",
                    headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
                    json={
                        "name": "Synthetic ingredient kitchen",
                        "username": "cook",
                        "password": "synthetic ingredient password",
                        "timezone": "Europe/Zurich",
                        "device_id": device,
                    },
                )
                setup.raise_for_status()
                operator.headers["Authorization"] = "Bearer " + setup.json()["access_token"]
                recipe_id = str(uuid4())
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

                add(
                    "recipe",
                    {
                        "title": "Synthetic imported soup",
                        "servings": "2",
                        "source_platform": "website",
                        "ingredients": [
                            {
                                "id": str(uuid4()),
                                "name": "zwibel",
                                "quantity": "2",
                                "unit": "Handvoll",
                                "original_text": "2 Handvoll zwibel",
                            }
                        ],
                        "steps": ["Cook until tender."],
                    },
                    recipe_id,
                )
                add(
                    "recipe",
                    {
                        "title": "Synthetic cupboard recipe",
                        "servings": "2",
                        "ingredients": [
                            {
                                "id": str(uuid4()),
                                "name": "Kreuzkümmel",
                                "quantity": "1",
                                "unit": "tsp",
                            }
                        ],
                        "steps": ["Toast the seeds."],
                    },
                )
                for name in [
                    "Zwiebeln",
                    "Olivenöl",
                    "Rice",
                    "Eggs",
                    "Butter",
                    "Long custom pantry ingredient without a catalogue entry",
                ]:
                    add("pantry", {"name": name, "available": True})
                operator.post("/api/v1/sync/push", json={"mutations": mutations}).raise_for_status()
                with sync_playwright() as p:
                    browser = (
                        p.chromium.launch(
                            executable_path=shutil.which("chromium")
                            or shutil.which("google-chrome"),
                            args=["--no-sandbox"],
                        )
                        if engine == "chromium"
                        else p.webkit.launch()
                    )
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 1000}, has_touch=True
                    )
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base + "/app/")
                    page.get_by_role("button", name="Open your kitchen", exact=True).click()
                    page.get_by_label("Username", exact=True).fill("cook")
                    page.get_by_label("Password", exact=True).fill("synthetic ingredient password")
                    page.get_by_role("button", name="Sign in", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text(
                        "Up to date", timeout=20000
                    )

                    def audit_shot(name):
                        assert page.evaluate(
                            "document.documentElement.scrollWidth <= innerWidth"
                        ), name
                        page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                        violations = page.evaluate(
                            "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))"
                        )
                        assert not violations, violations
                        if capture:
                            expect(page.locator(".toast")).not_to_be_visible()
                            page.evaluate("scrollTo(0,0)")
                            page.screenshot(
                                path=str(captures / (name + ".png")),
                                full_page=True,
                                animations="disabled",
                            )

                    navigate(page, "Pantry")
                    expect(page.locator(".pantry-emoji")).to_have_count(6)
                    assert (
                        page.locator(".pantry-item")
                        .filter(has=page.get_by_text("Zwiebeln", exact=True))
                        .evaluate("el=>el.getBoundingClientRect().height <= 64")
                    )
                    audit_shot("pantry-desktop")
                    page.get_by_label("Include in shopping this week").first.click()
                    expect(page.get_by_label("Include in shopping this week").first).to_be_checked()
                    page.get_by_label("In the cupboard · Rice", exact=True).click()
                    expect(
                        page.get_by_label("In the cupboard · Rice", exact=True)
                    ).not_to_be_checked()
                    navigate(page, "Recipes")
                    page.get_by_role("button", name="Synthetic imported soup", exact=False).click()
                    page.get_by_role("button", name="Edit", exact=True).click()
                    expect(page.get_by_label("Custom unit", exact=True)).to_have_value("Handvoll")
                    field = page.get_by_role("combobox", name="Ingredient 1", exact=True)
                    field.focus()
                    expect(
                        page.get_by_role("option", name="Zwiebeln Pantry", exact=True)
                    ).to_be_visible()
                    audit_shot("suggestions-desktop")
                    page.wait_for_function("!!navigator.serviceWorker.controller")
                    if engine == "chromium":
                        context.set_offline(True)
                    field.press("ArrowDown")
                    field.press("Enter")
                    expect(field).to_have_value("Zwiebeln")
                    expect(
                        page.get_by_text("Original text: 2 Handvoll zwibel", exact=True)
                    ).to_be_visible()
                    page.get_by_label("Unit", exact=True).select_option("tbsp")
                    page.get_by_role("button", name="Add ingredient", exact=True).click()
                    second = page.get_by_role("combobox", name="Ingredient 2", exact=True)
                    second.fill("kreuzk")
                    expect(
                        page.get_by_role("option", name="Kreuzkümmel Recipes", exact=True)
                    ).to_be_visible()
                    second.press("Escape")
                    second.fill("Dragon fruit")
                    expect(
                        page.get_by_role("status").filter(has_text="New ingredient")
                    ).to_be_visible()
                    page.get_by_label("Unit", exact=True).nth(1).select_option("piece")
                    page.get_by_label("Quantity", exact=True).nth(1).fill("1")
                    page.get_by_role("button", name="Save", exact=True).click()
                    expect(page.locator(".recipe-editor")).not_to_be_visible()
                    if engine == "webkit":
                        page.wait_for_load_state("networkidle")
                        expect(page.locator(".connection-status")).to_have_text("Up to date")
                    page.reload()
                    navigate(page, "Recipes")
                    page.get_by_role("button", name="Synthetic imported soup", exact=False).click()
                    expect(page.locator(".ingredients-list")).to_contain_text("Zwiebeln")
                    expect(page.locator(".ingredients-list")).to_contain_text("Dragon fruit")
                    if engine == "chromium":
                        context.set_offline(False)
                    page.get_by_role("button", name="Sync now", exact=True).click()
                    expect(page.locator(".connection-status")).to_have_text(
                        "Up to date", timeout=20000
                    )
                    saved = operator.get("/api/v1/recipes/" + recipe_id).json()["payload"]
                    assert saved["ingredients"][0]["name"] == "Zwiebeln"
                    assert saved["ingredients"][0]["unit"] == "tbsp"
                    assert saved["ingredients"][0]["original_text"] == "2 Handvoll zwibel"
                    assert saved["ingredients"][1]["name"] == "Dragon fruit"
                    assert saved["ingredients"][1]["unit"] == "piece"
                    assert saved["ingredients"][1]["quantity"] == "1"
                    pantry = operator.get("/api/v1/pantry").json()["items"]
                    assert len(pantry) == 6  # Custom recipe ingredients do not invent pantry stock.
                    navigate(page, "Settings")
                    settings_section(page, "Your household")
                    page.get_by_label("Language", exact=True).select_option("de")
                    settings_section(page, "Design-Bibliothek")
                    page.get_by_role("radio", name="After Dark", exact=True).check()
                    page.set_viewport_size({"width": 390, "height": 844})
                    navigate(page, "Vorrat")
                    assert (
                        page.locator(".pantry-item")
                        .filter(has=page.get_by_text("Zwiebeln", exact=True))
                        .evaluate("el=>el.getBoundingClientRect().height <= 96")
                    )
                    assert page.locator(".pantry-item .check-row").evaluate_all(
                        "rows=>rows.every(row=>row.getBoundingClientRect().height>=44)"
                    )
                    audit_shot("pantry-phone-de-dark")
                    navigate(page, "Rezepte")
                    page.get_by_role("button", name="Synthetic imported soup", exact=False).click()
                    page.get_by_role("button", name="Bearbeiten", exact=True).click()
                    field = page.get_by_role("combobox", name="Zutat 1", exact=True)
                    field.fill("zwibel")
                    expect(
                        page.get_by_role("option", name="Zwiebeln Vorrat", exact=True)
                    ).to_be_visible()
                    audit_shot("suggestions-phone-de-dark")
                    page.get_by_role("option", name="Zwiebeln Vorrat", exact=True).tap()
                    page.get_by_label("Einheit", exact=True).first.select_option("__custom")
                    page.get_by_label("Eigene Einheit", exact=True).fill("Spritzer")
                    page.get_by_role("button", name="Speichern", exact=True).click()
                    navigate(page, "Settings")
                    settings_section(page, "Design-Bibliothek")
                    page.get_by_role("radio", name="Sunday", exact=True).check()
                    page.set_viewport_size({"width": 320, "height": 740})
                    navigate(page, "Vorrat")
                    audit_shot("pantry-320-de-sunday")
                    page.get_by_role("button", name="Vorrats-Basics wählen", exact=True).click()
                    expect(page.locator(".staple-option .pantry-emoji")).to_have_count(24)
                    audit_shot("pantry-basics-320-de-sunday")
                    navigate(page, "Rezepte")
                    page.get_by_role("button", name="Synthetic imported soup", exact=False).click()
                    page.get_by_role("button", name="Bearbeiten", exact=True).click()
                    expect(page.get_by_label("Eigene Einheit", exact=True)).to_have_value(
                        "Spritzer"
                    )
                    field = page.get_by_role("combobox", name="Zutat 1", exact=True)
                    field.fill("zwibel")
                    audit_shot("suggestions-320-de-sunday")
                    # Another device changes the pantry while a keyboard choice is active.
                    # Keep focus in the combobox: clicking Sync would itself reset selection.
                    shared_id = str(uuid4())

                    def shared_name(name, revision=0):
                        mid = str(uuid4())
                        operator.post(
                            "/api/v1/sync/push",
                            json={
                                "mutations": [
                                    {
                                        "mutation_id": mid,
                                        "idempotency_key": mid,
                                        "entity_id": shared_id,
                                        "kind": "pantry",
                                        "operation": "upsert",
                                        "base_revision": revision,
                                        "device_id": device,
                                        "client_timestamp": "2000-01-01T00:00:00Z",
                                        "payload": {"name": name, "available": True},
                                    }
                                ]
                            },
                        ).raise_for_status()
                        page.evaluate("dispatchEvent(new Event('online'))")

                    field.fill("zwi")
                    shared_name("Zwiebelpulver")
                    extra = page.get_by_role("option", name="Zwiebelpulver Vorrat", exact=True)
                    expect(extra).to_be_visible()
                    expect(page.locator(".connection-status")).to_have_text("Aktuell")
                    field.press("ArrowDown")
                    field.press("ArrowDown")
                    expect(extra).to_have_attribute("aria-selected", "true")
                    revision = next(
                        row["revision"]
                        for row in operator.get("/api/v1/pantry").json()["items"]
                        if row["id"] == shared_id
                    )
                    shared_name("__proto__", revision)
                    expect(extra).not_to_be_visible()
                    page.wait_for_function(
                        "document.querySelector('.ingredient-name-field input').getAttribute('aria-activedescendant') === null"
                    )
                    field.press("ArrowDown")
                    field.press("Enter")
                    expect(field).to_have_value("Zwiebeln")
                    navigate(page, "Vorrat")
                    reserved = page.locator(".pantry-item").filter(
                        has=page.get_by_text("__proto__", exact=True)
                    )
                    expect(reserved.locator(".pantry-emoji")).to_have_text("🥣")
                    assert not errors, errors
                    context.close()
                    browser.close()
                    print(
                        json.dumps(
                            {
                                "state": "passed",
                                "engine": engine,
                                "offline_reload_verified": engine == "chromium",
                                "scope": "Real SQLite, save/reload/sync (offline reload on Chromium), EN/DE, pantry controls, units/custom units, fuzzy/keyboard/touch suggestions, original text, Axe, 1440/390/320, three themes; synthetic household",
                            }
                        )
                    )
        finally:
            server.should_exit = True
            thread.join(timeout=5)


if __name__ == "__main__":
    main()
