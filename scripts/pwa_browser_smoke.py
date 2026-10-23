"""Real Chromium PWA flows, local backend, synthetic household. No external-service doubles.

Build frontend first. Captures are real renders; demo food is labelled illustrative.
"""

import json
import os
import shutil
import socket
import threading
import time
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from browser_navigation import navigate
from browser_settings import settings_section
from playwright.sync_api import expect, sync_playwright

from mealf.app import create_app


def main():
    with TemporaryDirectory(prefix="mealf-pwa-") as temporary:
        root = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        app = create_app(root, run_worker=False)
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
            raise RuntimeError("PWA server did not start")
        captures = Path(os.environ.get("MEALF_SCREENSHOT_DIR", ".impeccable/review/round-1"))
        captures.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=os.environ.get("CHROMIUM_EXECUTABLE")
                    or shutil.which("chromium")
                    or shutil.which("google-chrome"),
                    args=["--no-sandbox"],
                )
                errors = []
                context = browser.new_context(
                    viewport={"width": 1440, "height": 1000}, accept_downloads=True
                )
                page = context.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))

                axe = Path("frontend/node_modules/axe-core/axe.min.js").read_text()

                def audit(name, screen=page):
                    screen.evaluate(axe)
                    result = screen.evaluate(
                        "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>n.target)}))"
                    )
                    assert result == [], (name, result)

                def wait_server_rows(screen, path, ready):
                    deadline = time.monotonic() + 20
                    rows = []
                    while time.monotonic() < deadline:
                        rows = screen.evaluate(
                            "async path => (await (await fetch(path, {headers:{'X-Mealf-Client':'pwa'}})).json()).items",
                            path,
                        )
                        if ready(rows):
                            return rows
                        screen.wait_for_timeout(200)
                    raise AssertionError((path, rows))

                def capture(name):
                    if os.environ.get("MEALF_CAPTURE") == "1":
                        page.evaluate(
                            "async()=>{for(const image of document.images){if(image.complete)await image.decode().catch(()=>{});}}"
                        )
                        page.screenshot(
                            path=str(captures / name), animations="disabled", full_page=True
                        )

                page.goto(base + "/app/")
                expect(page).to_have_title("mealf — Your kitchen")
                expect(page.get_by_role("link", name="mealf", exact=True)).to_be_visible()
                expect(page.locator(".wordmark .brand-wordmark")).to_have_attribute(
                    "src", "/app/brand/wordmark-v1.png"
                )
                page.wait_for_function(
                    "[...document.querySelectorAll('.wordmark img,.welcome-icon')].every(image=>image.complete&&image.naturalWidth>0)"
                )
                expect(
                    page.get_by_role("heading", name="Get your hot buns in here.")
                ).to_be_visible()
                peach = page.locator(".welcome-content [data-peach]")
                peach.click()
                expect(page.locator("#peach-reaction")).to_have_text("Oh, fork me.")
                assert peach.locator("img").evaluate(
                    "image => image.getAnimations().some(a => a.effect.getKeyframes().length > 4)"
                )
                if os.environ.get("MEALF_CAPTURE") == "1":
                    # A genuine rendered contact frame; animation behavior is asserted above.
                    peach.evaluate(
                        "button => { for (const e of button.querySelectorAll('img,.peach-hand')) for (const a of e.getAnimations()) {a.pause();a.currentTime=168;} }"
                    )
                    page.screenshot(
                        path=str(captures / "peach-contact-desktop.png"),
                        animations="allow",
                        full_page=True,
                    )
                peach.click()
                expect(page.locator("#peach-reaction")).to_have_text(
                    "Harder. The dough, you menace."
                )
                peach.focus()
                peach.press("Enter")
                expect(page.locator("#peach-reaction")).to_have_text(
                    "Dinner first. Spanking later."
                )
                page.emulate_media(reduced_motion="reduce")
                peach.press("Space")
                expect(page.locator("#peach-reaction")).to_have_text(
                    "Tenderise the peach. Respect the chef."
                )
                assert peach.locator("img").evaluate("image => image.getAnimations().length === 0")
                page.get_by_role("combobox", name="Language", exact=True).select_option("de")
                page.set_viewport_size({"width": 390, "height": 844})
                page.emulate_media(color_scheme="dark", reduced_motion="reduce")
                peach.click()
                expect(page.locator("#peach-reaction")).to_have_text(
                    "Oh, leck mich. Den Löffel natürlich."
                )
                assert page.locator("#peach-reaction").evaluate(
                    "e => { const r=e.getBoundingClientRect(); return r.left>=15 && r.right<=innerWidth-15 && r.top>=7 && r.bottom<=innerHeight-7; }"
                )
                audit("peach reaction German dark reduced motion")
                capture("peach-reduced-phone-de-dark.png")
                page.get_by_role("combobox", name="Sprache", exact=True).select_option("en")
                page.set_viewport_size({"width": 1440, "height": 1000})
                page.emulate_media(color_scheme="light", reduced_motion="no-preference")
                expect(page.locator("#peach-reaction")).to_be_empty(timeout=5000)
                peach.evaluate("button => button.blur()")
                # App chrome does not accidentally select; recipe reading and inputs opt in.
                page.locator(".welcome-description").dblclick()
                assert page.evaluate("!window.getSelection()?.toString().trim()")
                page.evaluate("window.getSelection()?.removeAllRanges()")
                assert page.evaluate("""() => {
                    const event = new WheelEvent('wheel', {ctrlKey:true,cancelable:true});
                    document.dispatchEvent(event);
                    return event.defaultPrevented;
                }""")
                assert page.evaluate("""() => {
                    const event = new WheelEvent('wheel', {cancelable:true});
                    document.dispatchEvent(event);
                    return !event.defaultPrevented;
                }""")
                for gesture in ["gesturestart", "gesturechange", "gestureend"]:
                    assert page.evaluate(
                        """type => {
                        const event = new Event(type, {cancelable:true});
                        document.dispatchEvent(event);
                        return event.defaultPrevented;
                    }""",
                        gesture,
                    )
                touch_context = browser.new_context(
                    viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
                )
                touch_page = touch_context.new_page()
                touch_page.goto(base + "/app/")
                expect(touch_page.locator(".welcome-content")).to_be_visible()
                touch_session = touch_context.new_cdp_session(touch_page)
                touch_session.send(
                    "Input.synthesizePinchGesture",
                    {"x": 195, "y": 300, "scaleFactor": 1.8, "gestureSourceType": "touch"},
                )
                assert touch_page.evaluate("visualViewport.scale") == 1
                touch_page.touchscreen.tap(20, 200)
                touch_page.touchscreen.tap(20, 200)
                assert touch_page.evaluate("visualViewport.scale") == 1
                touch_page.get_by_role("button", name="Explore the demo").click()
                expect(
                    touch_page.get_by_role("heading", name="Your kitchen", exact=True)
                ).to_be_visible()
                touch_page.wait_for_function("document.documentElement.scrollHeight > innerHeight")
                touch_session.send(
                    "Input.dispatchTouchEvent",
                    {"type": "touchStart", "touchPoints": [{"x": 180, "y": 600}]},
                )
                for position in range(570, 299, -30):
                    touch_session.send(
                        "Input.dispatchTouchEvent",
                        {"type": "touchMove", "touchPoints": [{"x": 180, "y": position}]},
                    )
                    touch_page.wait_for_timeout(25)
                touch_session.send(
                    "Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}
                )
                touch_page.wait_for_function("scrollY > 0")
                touch_context.close()
                capture("pwa-welcome-desktop.png")
                page.set_viewport_size({"width": 390, "height": 844})
                capture("pwa-welcome-phone.png")
                page.emulate_media(color_scheme="dark")
                audit("branded welcome phone dark")
                capture("pwa-welcome-phone-dark.png")
                page.emulate_media(color_scheme="light")
                page.set_viewport_size({"width": 1440, "height": 1000})
                page.get_by_role("button", name="Explore the demo").click()
                expect(page.get_by_role("heading", name="Your kitchen", exact=True)).to_be_visible()
                expect(page.get_by_role("navigation", name="mealf", exact=True)).to_be_visible()
                expect(page.locator(".featured-meal img")).to_be_visible()
                audit("home desktop")
                capture("pwa-home-desktop.png")
                page.emulate_media(color_scheme="dark")
                capture("pwa-home-desktop-dark.png")
                page.emulate_media(color_scheme="light")
                page.set_viewport_size({"width": 390, "height": 844})
                capture("pwa-home-phone.png")
                page.emulate_media(color_scheme="dark")
                audit("home phone dark")
                capture("pwa-home-phone-dark.png")
                navigate(page, "Recipes")
                expect(page.get_by_role("heading", name="Recipes", exact=True)).to_be_visible()
                audit("recipes phone dark")
                capture("pwa-recipes-phone-dark.png")
                page.get_by_role("button", name="Creamy tomato pasta", exact=False).first.click()
                expect(page.get_by_role("heading", name="Creamy tomato pasta")).to_be_visible()
                page.locator(".method-list li").first.dblclick(position={"x": 55, "y": 12})
                assert page.evaluate("Boolean(window.getSelection()?.toString().trim())")
                page.evaluate("window.getSelection()?.removeAllRanges()")
                assert page.get_by_role("button", name="Edit", exact=True).evaluate(
                    "element => getComputedStyle(element).userSelect === 'none'"
                )
                page.get_by_role("button", name="Edit", exact=True).click()
                page.get_by_label("Recipe name", exact=True).select_text()
                assert page.get_by_label("Recipe name", exact=True).evaluate(
                    "element => element.selectionStart === 0 && element.selectionEnd === element.value.length"
                )
                page.get_by_label("Recipe name", exact=True).fill("Demo pasta edited offline")
                page.wait_for_function("!!navigator.serviceWorker.controller")
                context.set_offline(True)
                page.get_by_role("button", name="Save", exact=True).click()
                expect(page.get_by_role("heading", name="Recipes", exact=True)).to_be_visible()
                page.reload()
                expect(
                    page.get_by_role("button", name="Demo pasta edited offline", exact=False).first
                ).to_be_visible()
                # Shared public egg assets are cached; taps never navigate or lose offline work.
                page.locator(".app-footer [data-peach]").click()
                expect(page.locator("#peach-reaction")).not_to_be_empty()
                context.set_offline(False)
                navigate(page, "Settings")
                settings_section(page, "Your household")
                page.get_by_label("Language", exact=True).select_option("de")
                expect(page.get_by_role("heading", name="Einstellungen")).to_be_visible()
                expect(page.locator('a[href="/admin/"]')).to_have_count(0)
                expect(page.locator('a[href="/admin/#bring"]')).to_have_count(0)
                audit("settings phone German dark")
                capture("pwa-settings-phone-de-dark.png")
                navigate(page, "Kalender")
                expect(page.get_by_role("heading", name="Kalender", exact=True)).to_be_visible()
                audit("calendar phone German dark")
                capture("pwa-calendar-phone-de-dark.png")
                page.get_by_role("button", name="Demo verlassen").first.click()
                expect(
                    page.get_by_role("heading", name="Get your hot buns in here.")
                ).to_be_visible()
                # Demo never created a server household or library.
                assert not page.evaluate(
                    "async()=> (await (await fetch('/api/v1/system/info')).json()).configured"
                )
                page.emulate_media(color_scheme="light")
                page.get_by_role("button", name="Open your kitchen").click()
                expect(page.get_by_role("heading", name="Set up your kitchen")).to_be_visible()
                page.get_by_label("Username", exact=True).fill("cook")
                page.get_by_label("Password", exact=True).fill("synthetic pwa kitchen password")
                page.get_by_label("One-time setup token", exact=True).fill(
                    (root / "config/setup-token").read_text()
                )
                page.get_by_label("Kitchen name", exact=True).fill("Browser kitchen")
                page.get_by_label("Household time zone", exact=True).fill("Europe/Zurich")
                page.get_by_role("button", name="Set up your kitchen", exact=True).click()
                expect(page.get_by_role("heading", name="Your kitchen", exact=True)).to_be_visible(
                    timeout=15000
                )
                page.get_by_role("button", name="New recipe", exact=True).click()
                page.get_by_label("Recipe name", exact=True).fill("Offline test soup")
                page.get_by_role("button", name="Add ingredient", exact=True).click()
                page.get_by_role("combobox", name="Ingredient 1", exact=True).fill("Carrots")
                page.get_by_label("Quantity", exact=True).fill("1½")
                page.get_by_label("Unit", exact=True).select_option("kg")
                page.get_by_role("button", name="Add step", exact=True).click()
                page.get_by_label("Step 1", exact=True).fill("Simmer until tender.")
                page.wait_for_function("!!navigator.serviceWorker.controller")
                context.set_offline(True)
                page.get_by_role("button", name="Save", exact=True).click()
                expect(page.get_by_role("heading", name="Your kitchen", exact=True)).to_be_visible()
                navigate(page, "Recipes")
                expect(
                    page.get_by_role("button", name="Offline test soup", exact=False)
                ).to_be_visible()
                page.reload()
                expect(page.get_by_role("heading", name="Your kitchen", exact=True)).to_be_visible()
                navigate(page, "Recipes")
                expect(
                    page.get_by_role("button", name="Offline test soup", exact=False)
                ).to_be_visible()
                context.set_offline(False)
                page.get_by_role("button", name="Sync now", exact=True).click()
                expect(page.locator(".connection-status")).to_have_text("Up to date", timeout=15000)
                assert page.evaluate(
                    "async()=>{const r=await fetch('/api/v1/recipes',{headers:{'X-Mealf-Client':'pwa'}});const data=await r.json();return JSON.stringify(data).includes('Offline test soup');}"
                )
                # Second physical browser context = independent device session.
                second_context = browser.new_context(viewport={"width": 1100, "height": 900})
                second = second_context.new_page()
                second.on("pageerror", lambda error: errors.append(str(error)))
                second.goto(base + "/app/")
                second.get_by_role("button", name="Open your kitchen").click()
                expect(
                    second.get_by_role("heading", name="Get your hot buns in here.")
                ).to_be_visible()
                expect(second.locator(".welcome-household")).to_contain_text("Browser kitchen")
                audit("configured PWA login", second)
                if os.environ.get("MEALF_CAPTURE") == "1":
                    second.screenshot(path=str(captures / "pwa-login-desktop.png"), full_page=True)
                second.get_by_label("Username", exact=True).fill("cook")
                second.get_by_label("Password", exact=True).fill("synthetic pwa kitchen password")
                second.get_by_role("button", name="Sign in", exact=True).click()
                expect(
                    second.get_by_role("heading", name="Your kitchen", exact=True)
                ).to_be_visible(timeout=15000)
                navigate(second, "Recipes")
                expect(
                    second.get_by_role("button", name="Offline test soup", exact=False)
                ).to_be_visible(timeout=15000)
                second.get_by_role("button", name="Offline test soup", exact=False).click()
                expect(second.locator(".ingredient-amount")).to_have_text("1.5 kg")
                # Conflicting offline edits are ordered by server commits, then deletion
                # blocks a stale edit instead of resurrecting the old identity.
                context.set_offline(True)
                page.get_by_role("button", name="Offline test soup", exact=False).click()
                page.get_by_role("button", name="Edit", exact=True).click()
                page.get_by_label("Recipe name", exact=True).fill("Device A committed last")
                page.get_by_role("button", name="Save", exact=True).click()
                expect(
                    page.locator(".recipe-card").filter(has_text="Device A committed last")
                ).to_be_visible()
                second.get_by_role("button", name="Edit", exact=True).click()
                second.get_by_label("Recipe name", exact=True).fill("Device B committed first")
                second.get_by_role("button", name="Save", exact=True).click()
                expect(
                    second.locator(".recipe-card").filter(has_text="Device B committed first")
                ).to_be_visible()
                expect(second.locator(".connection-status")).to_have_text(
                    "Up to date", timeout=15000
                )
                context.set_offline(False)
                page.get_by_role("button", name="Sync now", exact=True).click()
                expect(page.locator(".connection-status")).to_have_text("Up to date", timeout=15000)
                second.get_by_role("button", name="Sync now", exact=True).click()
                expect(
                    second.locator(".recipe-card").filter(has_text="Device A committed last")
                ).to_be_visible(timeout=15000)
                second_context.set_offline(True)
                second.locator(".recipe-card").filter(has_text="Device A committed last").click()
                second.get_by_role("button", name="Edit", exact=True).click()
                second.get_by_label("Recipe name", exact=True).fill(
                    "Keep this rejected offline edit"
                )
                second.get_by_role("button", name="Save", exact=True).click()
                expect(
                    second.locator(".recipe-card").filter(
                        has_text="Keep this rejected offline edit"
                    )
                ).to_be_visible()
                page.locator(".recipe-card").filter(has_text="Device A committed last").click()
                page.get_by_role("button", name="Delete", exact=True).click()
                page.get_by_role("dialog").get_by_role("button", name="Delete", exact=True).click()
                expect(page.get_by_role("heading", name="Nothing to fork. Yet.")).to_be_visible()
                expect(page.locator(".connection-status")).to_have_text("Up to date", timeout=15000)
                second_context.set_offline(False)
                second.get_by_role("button", name="Sync now", exact=True).click()
                expect(
                    second.get_by_role("alert").filter(has_text="Changes need review")
                ).to_be_visible(timeout=15000)
                navigate(second, "Settings")
                second.get_by_role("button", name="Keep recipe as a new copy", exact=True).click()
                expect(second.locator(".connection-status")).to_have_text(
                    "Up to date", timeout=15000
                )
                navigate(second, "Recipes")
                expect(
                    second.locator(".recipe-card").filter(
                        has_text="Keep this rejected offline edit"
                    )
                ).to_be_visible()
                server_rows = second.evaluate(
                    "async()=> (await (await fetch('/api/v1/recipes',{headers:{'X-Mealf-Client':'pwa'}})).json()).items"
                )
                assert (
                    len(server_rows) == 1
                    and server_rows[0]["payload"]["title"] == "Keep this rejected offline edit"
                )
                # Calendar assignment, cooked leftovers and pantry use actual local mutations.
                second.locator(".recipe-card").filter(
                    has_text="Keep this rejected offline edit"
                ).click()
                second.get_by_role("button", name="Plan a meal", exact=True).click()
                plan = second.get_by_role("dialog", name="Plan a meal", exact=True)
                planned_day = plan.locator('input[type="date"]').first.input_value()
                plan.get_by_role("button", name="Save", exact=True).click()
                expect(plan).not_to_be_visible()
                expect(second.get_by_role("button", name="Plan a meal", exact=True)).to_be_focused()
                navigate(second, "Calendar")
                expect(
                    second.locator(".meal-open").filter(has_text="Keep this rejected offline edit")
                ).to_be_visible()
                second.get_by_role(
                    "button", name="Edit Keep this rejected offline edit", exact=True
                ).click()
                second.get_by_role("button", name="Record leftovers", exact=True).click()
                second.get_by_role("spinbutton", name="Remaining portions", exact=True).fill("2")
                second.get_by_role("dialog").get_by_role(
                    "button", name="Record leftovers", exact=True
                ).last.click()
                expect(second.get_by_role("dialog")).not_to_be_visible()
                expect(second.locator(".leftovers-section")).to_contain_text("2 Remaining portions")
                navigate(second, "Pantry")
                second.get_by_role("textbox", name="Staple name", exact=True).fill("Carrots")
                second.get_by_role("button", name="Add", exact=True).click()
                expect(second.locator(".pantry-item")).to_contain_text("Carrots")
                expect(second.locator(".connection-status")).to_have_text(
                    "Up to date", timeout=15000
                )
                override = second.get_by_role("checkbox", name="Include in shopping this week")
                override.click()
                expect(override).to_be_checked()
                # Wait for the committed payload, rather than a possibly stale status label.
                included = wait_server_rows(
                    second,
                    "/api/v1/pantry",
                    lambda rows: len(rows) == 1
                    and rows[0]["payload"]["include_this_week"] is True
                    and rows[0]["payload"]["include_week_start"] is not None,
                )
                period = included[0]["payload"]["include_week_start"]
                # The assignment date and pantry period use the same household civil calendar.
                day = date.fromisoformat(planned_day)
                assert period == (day - timedelta(days=day.weekday())).isoformat()
                override.click()
                expect(override).not_to_be_checked()
                wait_server_rows(
                    second,
                    "/api/v1/pantry",
                    lambda rows: len(rows) == 1
                    and rows[0]["payload"]["include_this_week"] is False
                    and rows[0]["payload"]["include_week_start"] is None,
                )
                server_meals = second.evaluate(
                    "async()=> (await (await fetch('/api/v1/calendar/meals',{headers:{'X-Mealf-Client':'pwa'}})).json()).items"
                )
                assert (
                    len(server_meals) == 1
                    and server_meals[0]["payload"]["cooked"]
                    and server_meals[0]["payload"]["date"] == planned_day
                )
                # Import structured user-supplied content through the actual persistent job handler.
                navigate(second, "Recipes")
                second.get_by_role("button", name="Import recipe", exact=True).click()
                source = {
                    "@context": "https://schema.org",
                    "@type": "Recipe",
                    "name": "Reviewed imported beans",
                    "recipeYield": "2",
                    "recipeIngredient": ["200 g beans"],
                    "recipeInstructions": ["Simmer until tender."],
                }
                second.locator(".import-alternative > summary").click()
                second.get_by_role("textbox", name="Recipe text", exact=True).fill(
                    '<script type="application/ld+json">' + json.dumps(source) + "</script>"
                )
                second.get_by_role("button", name="Prepare preview", exact=True).click()
                expect(second.locator(".import-job")).to_contain_text(
                    "Preparing preview", timeout=15000
                )
                expect(second.locator(".connection-status")).to_have_text(
                    "Up to date", timeout=15000
                )
                with app.state.database.connect() as db:
                    job = dict(
                        db.execute(
                            "SELECT * FROM background_job WHERE kind='recipe.import' ORDER BY rowid DESC LIMIT 1"
                        ).fetchone()
                    )
                app.state.process_job(job)
                second.get_by_role("button", name="Sync now", exact=True).click()
                second.get_by_role("button", name="Review", exact=True).click(timeout=15000)
                expect(second.get_by_role("heading", name="Review your import")).to_be_visible()
                assert (
                    second.evaluate(
                        "async()=> (await (await fetch('/api/v1/recipes',{headers:{'X-Mealf-Client':'pwa'}})).json()).items.length"
                    )
                    == 1
                )
                second.get_by_label("Recipe name", exact=True).fill("Explicitly reviewed beans")
                second.get_by_role("button", name="Save", exact=True).click()
                expect(second.get_by_role("heading", name="Recipes", exact=True)).to_be_visible()
                expect(second.locator(".connection-status")).to_have_text(
                    "Up to date", timeout=15000
                )
                final_rows = second.evaluate(
                    "async()=> (await (await fetch('/api/v1/recipes',{headers:{'X-Mealf-Client':'pwa'}})).json()).items"
                )
                assert len(final_rows) == 2 and any(
                    row["payload"]["title"] == "Explicitly reviewed beans" for row in final_rows
                )
                # Editing a reusable week is offline-safe and never rewrites existing meals.
                navigate(second, "Calendar")
                second.get_by_role("button", name="Week options", exact=True).click()
                second.get_by_role("textbox", name="Template name", exact=True).fill(
                    "Everyday week"
                )
                second.get_by_role("button", name="Save this week", exact=True).click()
                expect(second.get_by_role("dialog")).not_to_be_visible()
                second.get_by_role("button", name="Week options", exact=True).click()
                second.get_by_role("button", name="Edit template Everyday week", exact=True).click()
                template_editor = second.get_by_role("dialog", name="Edit template", exact=True)
                second_context.set_offline(True)
                template_editor.get_by_role("textbox", name="Template name", exact=True).fill(
                    "Quick lunches"
                )
                template_editor.get_by_role(
                    "combobox", name="Day of the week", exact=True
                ).select_option("4")
                template_editor.get_by_role(
                    "combobox", name="Meal category", exact=True
                ).select_option("lunch")
                template_editor.get_by_role("combobox", name="Recipe", exact=True).select_option(
                    label="Explicitly reviewed beans"
                )
                template_editor.get_by_role("button", name="Add a meal", exact=True).click()
                expect(template_editor.locator(".template-slot")).to_have_count(2)
                template_editor.get_by_role("button", name="Remove meal 2", exact=True).click()
                template_editor.get_by_role("textbox", name="Servings", exact=True).fill("0")
                template_editor.get_by_role("button", name="Save", exact=True).click()
                expect(template_editor.get_by_role("alert")).to_be_visible()
                template_editor.get_by_role("textbox", name="Servings", exact=True).fill("3,5")
                second.set_viewport_size({"width": 390, "height": 844})
                audit("template editor phone", second)
                assert template_editor.evaluate("el=>el.scrollWidth <= el.clientWidth")
                if os.environ.get("MEALF_CAPTURE") == "1":
                    second.screenshot(
                        path=str(captures / "pwa-template-editor.png"),
                        animations="disabled",
                        full_page=True,
                    )
                template_editor.get_by_role("button", name="Save", exact=True).click()
                expect(
                    second.get_by_role("dialog", name="Week options", exact=True)
                ).to_be_visible()
                second.get_by_role("button", name="Close", exact=True).click()
                second.reload()
                navigate(second, "Calendar")
                second.get_by_role("button", name="Week options", exact=True).click()
                second.get_by_role("button", name="Edit template Quick lunches", exact=True).click()
                expect(
                    template_editor.get_by_role("textbox", name="Servings", exact=True)
                ).to_have_value("3.5")
                expect(
                    template_editor.get_by_role("combobox", name="Day of the week", exact=True)
                ).to_have_value("4")
                template_editor.get_by_role("textbox", name="Template name", exact=True).fill(
                    "Not saved"
                )
                template_editor.get_by_role("button", name="Cancel", exact=True).click()
                expect(
                    second.get_by_role("button", name="Edit template Quick lunches", exact=True)
                ).to_be_visible()
                second.get_by_role("button", name="Close", exact=True).click()
                second_context.set_offline(False)
                second.get_by_role("button", name="Sync now", exact=True).click()
                server_templates = wait_server_rows(
                    second,
                    "/api/v1/templates",
                    lambda rows: len(rows) == 1 and rows[0]["payload"]["name"] == "Quick lunches",
                )
                slot = server_templates[0]["payload"]["meals"][0]
                assert (
                    slot["weekday"] == 4
                    and slot["category"] == "lunch"
                    and slot["servings"] == "3.5"
                )
                assert slot["recipe_id"] == next(
                    row["id"]
                    for row in final_rows
                    if row["payload"]["title"] == "Explicitly reviewed beans"
                )
                assert (
                    second.evaluate(
                        "async()=> (await (await fetch('/api/v1/calendar/meals',{headers:{'X-Mealf-Client':'pwa'}})).json()).items.length"
                    )
                    == 1
                )
                second.get_by_role("button", name="Next week", exact=True).click()
                second.get_by_role("button", name="Week options", exact=True).click()
                second.get_by_role("button", name="Apply template", exact=True).click()
                applied = wait_server_rows(
                    second, "/api/v1/calendar/meals", lambda rows: len(rows) == 2
                )
                expected_day = (
                    day - timedelta(days=day.weekday()) + timedelta(days=11)
                ).isoformat()
                assert any(
                    row["payload"]["date"] == expected_day
                    and row["payload"]["servings"] == "3.5"
                    and row["payload"]["category"] == "lunch"
                    for row in applied
                ), (expected_day, applied)
                # Shared household suggestion defaults, offline drafts and approved learning.
                navigate(second, "Settings")
                settings_section(second, "Your household")
                expect(second.locator('a[href="/admin/"]')).to_be_visible()
                settings_section(second, "Bring!")
                expect(second.locator('a[href="/admin/#bring"]')).to_be_visible()
                settings_section(second, "Meal suggestions")
                planning = second.locator(".settings-group").filter(
                    has=second.get_by_role("heading", name="Meal suggestions", exact=True)
                )
                planning.get_by_label("Breakfast", exact=True).check()
                planning.get_by_label("Lunch", exact=True).check()
                planning.get_by_label(
                    "Allow repeats after all available recipes have been used", exact=True
                ).check()
                planning.get_by_label("Prefer available leftovers", exact=True).uncheck()
                planning.get_by_label("Use a fixed number of portions", exact=True).check()
                planning.get_by_label("Servings", exact=True).fill("3,5")
                planning.get_by_role("button", name="Save suggestion settings", exact=True).click()
                expect(
                    second.get_by_text(
                        "Suggestion settings saved. Plans still need your approval.", exact=True
                    )
                ).to_be_visible()
                second.set_viewport_size({"width": 1440, "height": 1000})
                audit("shared planning settings desktop", second)
                if os.environ.get("MEALF_CAPTURE") == "1":
                    second.screenshot(
                        path=str(captures / "pwa-planning-settings-desktop.png"),
                        full_page=True,
                        animations="disabled",
                    )
                navigate(page, "Settings")
                page.get_by_role("button", name="Sync now", exact=True).click()
                settings_section(page, "Meal suggestions")
                first_planning = page.locator(".settings-group").filter(
                    has=page.get_by_role("heading", name="Meal suggestions", exact=True)
                )
                expect(first_planning.get_by_label("Servings", exact=True)).to_have_value("3.5")
                expect(first_planning.get_by_label("Breakfast", exact=True)).to_be_checked()
                settings_section(second, "Your household")
                second.get_by_label("Language", exact=True).select_option("de")
                second.set_viewport_size({"width": 390, "height": 844})
                second.emulate_media(color_scheme="dark")
                audit("shared planning settings phone German dark", second)
                if os.environ.get("MEALF_CAPTURE") == "1":
                    second.screenshot(
                        path=str(captures / "pwa-planning-settings-phone-de-dark.png"),
                        full_page=True,
                        animations="disabled",
                    )
                settings_section(second, "Dein Haushalt")
                second.get_by_label("Sprache", exact=True).select_option("en")
                second_context.set_offline(True)
                planning.get_by_label("Servings", exact=True).fill("4.5")
                second.reload()
                navigate(second, "Settings")
                settings_section(second, "Meal suggestions")
                expect(planning.get_by_label("Servings", exact=True)).to_have_value("4.5")
                # An unsaved draft does not change cached or server-wide suggestion defaults.
                navigate(second, "Calendar")
                second.get_by_role("button", name="Next week", exact=True).click()
                second.get_by_role("button", name="Next week", exact=True).click()
                second.get_by_role("button", name="Suggest meals", exact=True).click()
                preview = second.get_by_role("dialog", name="A little inspiration", exact=True)
                expect(preview.locator(".suggestion-row")).to_have_count(21)
                expect(preview.get_by_text("3.5 servings", exact=True)).to_have_count(21)
                audit("offline shared preference suggestion preview phone", second)
                if os.environ.get("MEALF_CAPTURE") == "1":
                    second.screenshot(
                        path=str(captures / "pwa-planning-preview-phone.png"),
                        full_page=True,
                        animations="disabled",
                    )
                # Two same-turn activations must produce only one optimistic approval batch.
                preview.get_by_role("button", name="Add to calendar", exact=True).evaluate(
                    "button=>{button.click();button.click();}"
                )
                expect(preview).not_to_be_visible()
                queued = second.evaluate("""async()=>{
                  const name=(await indexedDB.databases()).find(item=>item.name.startsWith('mealf:')).name;
                  return new Promise((resolve,reject)=>{const opening=indexedDB.open(name);opening.onerror=()=>reject(opening.error);
                    opening.onsuccess=()=>{const db=opening.result,tx=db.transaction('outbox'),query=tx.objectStore('outbox').getAll();
                      query.onsuccess=()=>resolve(query.result.map(row=>row.approval?.request_id));
                      query.onerror=()=>reject(query.error);tx.oncomplete=()=>db.close();};});
                }""")
                assert len(queued) == 21 and len(set(queued)) == 1 and queued[0] is not None
                # Only the two prior meals exist remotely until this device reconnects.
                assert (
                    page.evaluate(
                        "async()=> (await(await fetch('/api/v1/calendar/meals',{headers:{'X-Mealf-Client':'pwa'}})).json()).items.length"
                    )
                    == 2
                )
                second_context.set_offline(False)
                second.get_by_role("button", name="Sync now", exact=True).click()
                added = wait_server_rows(
                    second, "/api/v1/calendar/meals", lambda rows: len(rows) == 23
                )
                approved = [row for row in added if row["payload"]["date"] > expected_day]
                assert len(approved) == 21 and all(
                    row["payload"]["servings"] == "3.5" for row in approved
                )
                learning = second.evaluate(
                    "async()=> (await(await fetch('/api/v1/household/planning-preferences',{headers:{'X-Mealf-Client':'pwa'}})).json())"
                )
                assert learning["accepted_counts"] and all(
                    count == 1 for count in learning["accepted_counts"].values()
                )
                navigate(second, "Settings")
                settings_section(second, "Meal suggestions")
                expect(planning.get_by_label("Servings", exact=True)).to_have_value("4.5")
                planning.get_by_role("button", name="Save suggestion settings", exact=True).click()
                expect(
                    second.get_by_text(
                        "Suggestion settings saved. Plans still need your approval.", exact=True
                    )
                ).to_be_visible()
                assert (
                    second.evaluate(
                        "async()=> (await(await fetch('/api/v1/household/planning-preferences',{headers:{'X-Mealf-Client':'pwa'}})).json()).preferences.servings"
                    )
                    == "4.5"
                )
                second_context.close()
                # Worker cache contains public shell assets, never authenticated API/media.
                cached = page.evaluate(
                    "async()=>{const result=[];for(const key of await caches.keys()){for(const request of await (await caches.open(key)).keys())result.push(new URL(request.url).pathname);}return result;}"
                )
                assert cached and all(path.startswith("/app/") for path in cached), cached
                brand_paths = ["/app/brand/peach-v1.png", "/app/brand/wordmark-v1.png"]
                assert all(path in cached for path in brand_paths)
                context.set_offline(True)
                assert page.evaluate(
                    "async paths => (await Promise.all(paths.map(async path => (await fetch(path)).ok))).every(Boolean)",
                    brand_paths,
                )
                context.set_offline(False)
                assert not errors, errors
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                context.close()
                browser.close()
                print(
                    "PWA real-browser smoke passed: isolated demo, English/German dark/mobile, setup, offline edit/reload, exact fractions, independent cookie sessions, commit-ordered conflicts, deletion/rejected-copy recovery, meal assignment, cooked leftovers, week-bound pantry overrides, explicit import review, offline template editing/reload/cancel and next-week application, axe WCAG checks shared suggestion settings across devices, offline preference drafts/previews and approval learning, and public-shell-only cache."
                )
        finally:
            server.should_exit = True
            thread.join(timeout=10)


if __name__ == "__main__":
    main()
