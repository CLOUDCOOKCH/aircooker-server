"""Phone safe-area/focus regressions in real browser engines, using synthetic data.

CSS safe-area values are injected to exercise notch geometry on Linux. This is not a
physical iPhone, Home Screen installation or software-keyboard test.
"""

import json
import os
import shutil
import socket
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from playwright.sync_api import expect, sync_playwright

from aircooker.app import create_app


def main():
    engine = os.environ.get("AIRCOOKER_LAYOUT_ENGINE", "chromium")
    captures = Path(os.environ.get("AIRCOOKER_SCREENSHOT_DIR", "build/pwa-layout")) / engine
    captures.mkdir(parents=True, exist_ok=True)
    evidence = []
    with TemporaryDirectory(prefix="mealf-layout-") as temporary:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        server = uvicorn.Server(
            uvicorn.Config(
                create_app(Path(temporary), run_worker=False),
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
            else:
                raise RuntimeError("Layout test backend not ready")
            with sync_playwright() as playwright:
                options = {}
                if engine == "chromium":
                    options = {
                        "executable_path": os.environ.get("CHROMIUM_EXECUTABLE")
                        or shutil.which("chromium")
                        or shutil.which("google-chrome"),
                        "args": ["--no-sandbox"],
                    }
                browser = playwright.chromium.launch(**options) if engine == "chromium" else None
                for name, width, height, safe, language in [
                    ("phone", 390, 844, [59, 0, 34, 0], "en"),
                    ("phone-dark", 390, 844, [59, 0, 34, 0], "de"),
                    ("small-phone", 320, 568, [20, 0, 0, 0], "en"),
                    ("landscape", 844, 390, [0, 59, 21, 59], "de"),
                    ("asymmetric-landscape", 852, 393, [0, 0, 21, 59], "en"),
                    ("desktop", 1440, 1000, [0, 0, 0, 0], "en"),
                ]:
                    mobile = width < 1000
                    context_options = {
                        "viewport": {"width": width, "height": height},
                        "is_mobile": mobile,
                        "has_touch": mobile,
                        "color_scheme": "dark" if language == "de" else "light",
                    }
                    # WebKit's ephemeral session rejects Blob staging for IndexedDB.
                    # Use real disposable disk storage, as an installed app does.
                    context = (
                        browser.new_context(**context_options)
                        if browser
                        else playwright.webkit.launch_persistent_context(
                            str(Path(temporary) / ("profile-" + name)), **context_options
                        )
                    )
                    page = context.new_page()
                    page.goto(base + "/app/")
                    expect(page.locator(".welcome-content")).to_be_visible()
                    # These are simulated safe areas, not OS-provided test evidence.
                    page.evaluate(
                        """safe => {
                        for (const [i, edge] of ['top','right','bottom','left'].entries())
                            document.documentElement.style.setProperty('--safe-'+edge,safe[i]+'px');
                        }""",
                        safe,
                    )
                    if language == "de":
                        page.locator(".welcome-header select").select_option("de")

                    def check(stage, selector=None):
                        metrics = page.evaluate(
                            """selector => {
                            const rect = e => {const r=e.getBoundingClientRect();
                                return {left:r.left,right:r.right,top:r.top,bottom:r.bottom};};
                            return {
                                scale:visualViewport.scale,
                                width:innerWidth, client:document.documentElement.clientWidth,
                                scroll:document.documentElement.scrollWidth,
                                fields:[...document.querySelectorAll('input,select,textarea')]
                                    .filter(e=>e.getClientRects().length)
                                    .map(e=>({tag:e.tagName,size:parseFloat(getComputedStyle(e).fontSize)})),
                                target:selector ? rect(document.querySelector(selector)) : null
                            }; }""",
                            selector,
                        )
                        assert abs(metrics["scale"] - 1) < 0.01, (name, stage, metrics)
                        assert metrics["scroll"] <= width + 1, (name, stage, metrics)
                        assert metrics["width"] == metrics["client"] == width, metrics
                        if mobile:
                            assert all(f["size"] >= 16 for f in metrics["fields"]), metrics
                        if metrics["target"]:
                            box = metrics["target"]
                            assert box["left"] >= safe[3] - 1, (name, stage, box)
                            assert box["right"] <= width - safe[1] + 1, (name, stage, box)
                            if (selector == ".app-nav" and mobile) or selector == ".sheet":
                                assert box["top"] >= safe[0] - 1, (name, stage, box)
                                assert box["bottom"] <= height - safe[2] + 1, (name, stage, box)
                        evidence.append({"variant": name, "stage": stage, **metrics})

                    check("welcome", ".welcome-header")
                    assert page.locator(".welcome-header").bounding_box()["y"] >= safe[0]
                    page.locator(".welcome-primary").click()
                    expect(page.locator(".welcome-form")).to_be_visible()
                    for field in page.locator(".welcome-form input").all():
                        field.click()
                        check("setup focus")
                    page.locator(".welcome-form input").first.evaluate("e=>e.blur()")
                    page.screenshot(path=str(captures / f"{name}-setup.png"))
                    # Return to the welcome view without writing a household or clearing storage.
                    page.locator(".welcome-form .text-button").click()
                    page.get_by_role(
                        "button", name="Demo entdecken" if language == "de" else "Explore the demo"
                    ).click()
                    expect(page.locator(".app-nav")).to_be_visible()
                    nav = page.locator(".nav-links")
                    if language == "de":
                        nav.get_by_role("button", name="Settings").click()
                        page.get_by_label("Language", exact=True).select_option("de")
                        nav.get_by_role("button", name="Start", exact=True).click()
                    if mobile:
                        expect(page.locator(".nav-brand")).to_be_hidden()
                    check("home", ".app-nav")
                    page.screenshot(path=str(captures / f"{name}-home.png"))
                    nav.get_by_role(
                        "button", name="Rezepte" if language == "de" else "Recipes"
                    ).click()
                    expect(page.locator(".recipe-card").first).to_be_visible()
                    check("recipes")
                    page.locator(".search-field input").click()
                    check("search focus")
                    page.locator(".recipe-card").first.click()
                    expect(page.locator(".servings-control input")).to_be_visible()
                    page.locator(".servings-control input").click()
                    check("servings focus")
                    page.get_by_role(
                        "button", name="Bearbeiten" if language == "de" else "Edit", exact=True
                    ).click()
                    expect(page.locator(".recipe-editor")).to_be_visible()
                    check("editor")
                    page.screenshot(path=str(captures / f"{name}-editor.png"))
                    page.get_by_role(
                        "button", name="Zurück" if language == "de" else "Back", exact=True
                    ).click()
                    nav.get_by_role(
                        "button", name="Kalender" if language == "de" else "Calendar"
                    ).click()
                    views = page.locator(".calendar-view-switch")
                    views.get_by_role(
                        "button", name="3 Tage" if language == "de" else "3 days", exact=True
                    ).click()
                    expect(page.locator(".calendar-day")).to_have_count(3)
                    check("three-day view")
                    page.screenshot(path=str(captures / f"{name}-three-days.png"))
                    # Actual narrow Plan a meal form, including WebKit's native date input.
                    page.locator(".calendar-slot .slot-heading button").first.click()
                    dialog = page.locator(".sheet")
                    expect(dialog).to_be_visible()
                    check("plan meal", ".sheet")
                    assert dialog.locator(".form-row").evaluate("""row => {
                        const labels=[...row.querySelectorAll('label')];
                        const controls=labels.map(l=>l.querySelector('input,select'));
                        const a=controls[0].getBoundingClientRect(), b=controls[1].getBoundingClientRect();
                        return controls.every((c,i)=>{const r=c.getBoundingClientRect(),l=labels[i].getBoundingClientRect();
                            return r.left>=l.left-1 && r.right<=l.right+1;}) &&
                            (a.bottom<=b.top || a.right<=b.left);
                    }""")
                    page.screenshot(path=str(captures / f"{name}-plan-meal.png"))
                    dialog.locator(".sheet-heading button").click()
                    if name == "phone":
                        # Trusted touch events in Chromium; real mouse PointerEvents in WebKit.
                        # Both exercise the same grip/capture/drop path without dispatching fake DOM drops.
                        source = page.locator(".calendar-week .meal-row").first
                        meal_id = source.get_attribute("data-meal-id")
                        grip = source.locator(".meal-drag-handle")
                        grip.evaluate(
                            "e=>e.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'})"
                        )
                        target = (
                            page.locator(".calendar-day").nth(1).locator('[data-category="lunch"]')
                        )
                        source_date = source.locator("xpath=..").get_attribute("data-date")
                        target_date = target.get_attribute("data-date")
                        a = grip.bounding_box()
                        b = target.bounding_box()
                        sx, sy = a["x"] + a["width"] / 2, a["y"] + a["height"] / 2
                        dx, dy = b["x"] + b["width"] / 2, b["y"] + 40
                        if engine == "chromium":
                            page.wait_for_function("!!navigator.serviceWorker.controller")
                            context.set_offline(True)
                            session = context.new_cdp_session(page)
                            session.send(
                                "Input.dispatchTouchEvent",
                                {"type": "touchStart", "touchPoints": [{"x": sx, "y": sy}]},
                            )
                            for step in range(1, 11):
                                session.send(
                                    "Input.dispatchTouchEvent",
                                    {
                                        "type": "touchMove",
                                        "touchPoints": [
                                            {
                                                "x": sx + (dx - sx) * step / 10,
                                                "y": sy + (dy - sy) * step / 10,
                                            }
                                        ],
                                    },
                                )
                                page.wait_for_timeout(30)
                            expect(page.locator(".is-drop-target")).to_have_attribute(
                                "data-date", target_date
                            )
                            page.screenshot(path=str(captures / "phone-dragging.png"))
                            session.send(
                                "Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}
                            )
                        else:
                            page.mouse.move(sx, sy)
                            page.mouse.down()
                            page.mouse.move(dx, dy, steps=12)
                            expect(page.locator(".is-drop-target")).to_have_attribute(
                                "data-date", target_date
                            )
                            page.mouse.up()
                        moved = page.locator(
                            f'[data-date="{target_date}"][data-category="lunch"] [data-meal-id="{meal_id}"]'
                        )
                        expect(moved).to_be_visible()
                        expect(page.locator(".meal-drag-preview")).to_have_count(0)
                        expect(page.locator(".sheet")).to_have_count(0)
                        expect(
                            page.locator(f'[data-date="{source_date}"] [data-meal-id="{meal_id}"]')
                        ).to_have_count(0)
                        page.reload()
                        expect(page.locator(".app-nav")).to_be_visible()
                        page.locator(".nav-links").get_by_role(
                            "button", name="Calendar", exact=True
                        ).click()
                        expect(page.locator(".calendar-week")).to_have_attribute(
                            "data-view", "three"
                        )
                        expect(moved).to_be_visible()
                        context.set_offline(False)
                        moved.locator(".meal-drag-handle").tap()
                        expect(page.locator(".sheet")).to_be_visible()
                        page.locator(".sheet .sheet-heading button").click()
                        # Keyboard-accessible move form remains available on the grip.
                        moved.locator(".meal-drag-handle").focus()
                        moved.locator(".meal-drag-handle").press("Enter")
                        expect(page.locator(".sheet")).to_be_visible()
                        page.locator(".sheet .sheet-heading button").click()
                    views.get_by_role(
                        "button", name="Woche" if language == "de" else "Week", exact=True
                    ).click()
                    expect(page.locator(".calendar-day")).to_have_count(7)
                    check("week view")
                    page.screenshot(path=str(captures / f"{name}-week.png"))
                    if name == "phone":
                        # Hold a grip near the scroll edge, then cancel; no meal write may occur.
                        row = page.locator(f'[data-meal-id="{meal_id}"]')
                        handle = row.locator(".meal-drag-handle")
                        handle.evaluate(
                            "e=>e.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'})"
                        )
                        a = handle.bounding_box()
                        g = page.locator(".calendar-week").bounding_box()
                        before = page.locator(".calendar-week").evaluate("e=>e.scrollLeft")
                        page.mouse.move(a["x"] + 22, a["y"] + 22)
                        page.mouse.down()
                        page.mouse.move(
                            min(width - 24, g["x"] + g["width"] - 8), a["y"] + 22, steps=10
                        )
                        page.wait_for_timeout(500)
                        assert (
                            page.locator(".calendar-week").evaluate("e=>e.scrollLeft") > before + 20
                        )
                        page.keyboard.press("Escape")
                        page.mouse.up()
                        page.wait_for_timeout(50)
                        expect(page.locator(".sheet")).to_have_count(0)
                        expect(page.locator(".meal-drag-preview")).to_have_count(0)
                        expect(
                            page.locator(f'[data-date="{target_date}"] [data-meal-id="{meal_id}"]')
                        ).to_have_count(1)
                        if engine == "chromium":
                            # Ordinary finger scrolling stays native outside the grips.
                            page.locator(".calendar-week").evaluate("e=>e.scrollLeft=0")
                            g = page.locator(".calendar-week").bounding_box()
                            y = max(90, g["y"] + 28)
                            session.send(
                                "Input.dispatchTouchEvent",
                                {"type": "touchStart", "touchPoints": [{"x": width - 65, "y": y}]},
                            )
                            for x in range(width - 85, 65, -20):
                                session.send(
                                    "Input.dispatchTouchEvent",
                                    {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]},
                                )
                                page.wait_for_timeout(25)
                            session.send(
                                "Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}
                            )
                            page.wait_for_function(
                                "document.querySelector('.calendar-week').scrollLeft>20"
                            )
                            # Native cancellation must clear the drag without moving the meal.
                            handle.evaluate(
                                "e=>e.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'})"
                            )
                            a = handle.bounding_box()
                            page.wait_for_timeout(250)
                            a = handle.bounding_box()
                            session.send(
                                "Input.dispatchTouchEvent",
                                {
                                    "type": "touchStart",
                                    "touchPoints": [{"x": a["x"] + 22, "y": a["y"] + 22}],
                                },
                            )
                            for step in range(1, 4):
                                session.send(
                                    "Input.dispatchTouchEvent",
                                    {
                                        "type": "touchMove",
                                        "touchPoints": [
                                            {
                                                "x": a["x"] + 22 + step * 10,
                                                "y": a["y"] + 22 - step * 4,
                                            }
                                        ],
                                    },
                                )
                                page.wait_for_timeout(30)
                            expect(page.locator(".meal-drag-preview")).to_be_visible()
                            session.send(
                                "Input.dispatchTouchEvent",
                                {"type": "touchCancel", "touchPoints": []},
                            )
                            expect(page.locator(".meal-drag-preview")).to_have_count(0)
                            expect(
                                page.locator(
                                    f'[data-date="{target_date}"] [data-meal-id="{meal_id}"]'
                                )
                            ).to_have_count(1)
                    views.get_by_role(
                        "button", name="Tag" if language == "de" else "Day", exact=True
                    ).click()
                    expect(page.locator(".calendar-day")).to_have_count(1)
                    page.get_by_role(
                        "button", name="Wochenoptionen" if language == "de" else "Week options"
                    ).click()
                    expect(page.locator(".sheet")).to_be_visible()
                    check("sheet", ".sheet")
                    page.screenshot(path=str(captures / f"{name}-sheet.png"))
                    context.close()
                if browser:
                    browser.close()
        finally:
            server.should_exit = True
            thread.join(timeout=10)
    (captures / "geometry.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"PASS: {engine} mobile focus, document width, notch geometry, landscape nav and sheets")


if __name__ == "__main__":
    main()
