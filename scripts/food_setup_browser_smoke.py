"""Real pantry/taste onboarding and durable sync; only provider HTTP is synthetic."""

import json
import os
import shutil
import socket
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

import httpx
import uvicorn
from browser_navigation import navigate
from browser_settings import settings_section
from playwright.sync_api import expect, sync_playwright

from mealf.ai import provider_for
from mealf.app import create_app


def main():
    captures = Path(os.environ.get("MEALF_FOOD_SCREENSHOT_DIR", "build/food-setup-browser"))
    captures.mkdir(parents=True, exist_ok=True)
    engine = os.environ.get("MEALF_LAYOUT_ENGINE", "chromium")
    assert engine in {"chromium", "webkit"}
    calls = []

    def transport(request):
        body = json.loads(request.content)
        source = json.loads(json.loads(body["contents"][0]["parts"][0]["text"])["untrusted_source"])
        calls.append(source)
        ideas = {
            "ideas": [
                {
                    "title": title,
                    "description": "Synthetic browser fixture.",
                    "servings": "2",
                    "ingredients": [{"name": "Pasta", "quantity": "200", "unit": "g"}],
                    "steps": ["Cook thoroughly."],
                }
                for title in ("Pasta one", "Pasta two", "Pasta three")
            ]
        }
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(ideas)}]}}
                ]
            },
        )

    with TemporaryDirectory(prefix="mealf-food-") as directory:
        root = Path(directory)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        os.environ["LOG_SETUP_TOKEN"] = "false"
        with patch(
            "mealf.app.provider_for",
            lambda config: provider_for(config, httpx.MockTransport(transport)),
        ):
            server = uvicorn.Server(
                uvicorn.Config(
                    create_app(root),
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
                with httpx.Client(base_url=base, trust_env=False) as operator:
                    response = operator.post(
                        "/api/v1/setup",
                        headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
                        json={
                            "name": "Synthetic food kitchen",
                            "username": "cook",
                            "password": "synthetic food password",
                            "timezone": "Europe/Zurich",
                            "device_id": str(uuid4()),
                        },
                    )
                    response.raise_for_status()
                    operator.headers["Authorization"] = "Bearer " + response.json()["access_token"]
                    operator.put(
                        "/api/v1/admin/ai",
                        json={
                            "provider": "gemini",
                            "model": "synthetic-model",
                            "api_key": "synthetic-only",
                            "input_formats": ["text"],
                        },
                    ).raise_for_status()
                    with sync_playwright() as playwright:
                        browser = (
                            playwright.chromium.launch(
                                executable_path=shutil.which("chromium")
                                or shutil.which("google-chrome"),
                                args=["--no-sandbox"],
                            )
                            if engine == "chromium"
                            else playwright.webkit.launch()
                        )
                        context = browser.new_context(
                            viewport={"width": 1440, "height": 1000}, has_touch=True
                        )
                        page = context.new_page()
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))

                        def audit():
                            page.evaluate(
                                Path("frontend/node_modules/axe-core/axe.min.js").read_text()
                            )
                            violations = page.evaluate(
                                "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                            )
                            assert not violations, [
                                (v["id"], v["nodes"][0]["html"]) for v in violations
                            ]
                            assert page.evaluate(
                                "document.documentElement.scrollWidth <= innerWidth"
                            ), "horizontal overflow"

                        def capture(name):
                            audit()
                            if os.environ.get("MEALF_CAPTURE") == "1":
                                page.evaluate("scrollTo(0,0)")
                                page.screenshot(
                                    path=str(captures / name), full_page=True, animations="disabled"
                                )

                        page.goto(base + "/app/")
                        page.get_by_role("button", name="Open your kitchen", exact=True).click()
                        page.get_by_label("Username", exact=True).fill("cook")
                        page.get_by_label("Password", exact=True).fill("synthetic food password")
                        page.get_by_role("button", name="Sign in", exact=True).click()
                        expect(
                            page.get_by_role(
                                "heading", name="What’s already in your kitchen?", exact=True
                            )
                        ).to_be_visible()
                        capture("welcome-desktop.png")
                        page.get_by_role("button", name="Choose pantry basics", exact=True).click()
                        for name in ("Salt", "Olive oil", "Rice"):
                            page.get_by_role("checkbox", name=name, exact=True).check()
                        capture("pantry-desktop.png")
                        page.set_viewport_size({"width": 390, "height": 844})
                        capture("pantry-mobile.png")
                        context.set_offline(engine == "chromium")
                        page.get_by_role("button", name="Save my pantry", exact=True).click()
                        expect(
                            page.get_by_role("heading", name="Pantry", exact=True)
                        ).to_be_visible()
                        page.reload()
                        expect(
                            page.get_by_role("heading", name="Your kitchen", exact=True)
                        ).to_be_visible()
                        context.set_offline(False)
                        page.get_by_role("button", name="Sync now", exact=True).click()
                        for _ in range(100):
                            if operator.get("/api/v1/household/food-profile").json()["profile"][
                                "pantry_setup_done"
                            ]:
                                break
                            page.wait_for_timeout(100)
                        pantry = operator.get("/api/v1/pantry").json()["items"]
                        assert sorted(row["payload"]["name"] for row in pantry) == [
                            "Olive oil",
                            "Rice",
                            "Salt",
                        ], pantry
                        page.get_by_role("button", name="Recipe ideas", exact=False).click()
                        expect(page.get_by_role("heading", name="Rice", exact=True)).to_be_visible()
                        capture("taste-mobile.png")
                        card = page.locator(".taste-card").bounding_box()
                        if engine == "chromium":
                            touch = context.new_cdp_session(page)
                            x, y = card["x"] + 80, card["y"] + 100
                            touch.send(
                                "Input.dispatchTouchEvent",
                                {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]},
                            )
                            for step in range(1, 9):
                                touch.send(
                                    "Input.dispatchTouchEvent",
                                    {
                                        "type": "touchMove",
                                        "touchPoints": [{"x": x + step * 14, "y": y}],
                                    },
                                )
                            touch.send(
                                "Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}
                            )
                            touch.detach()
                        else:
                            # WebKit automation exposes trusted mouse pointers; device touch remains unverified.
                            page.mouse.move(card["x"] + 80, card["y"] + 100)
                            page.mouse.down()
                            page.mouse.move(card["x"] + 190, card["y"] + 100, steps=8)
                            page.mouse.up()
                        expect(
                            page.get_by_role("heading", name="Pasta", exact=True)
                        ).to_be_visible()
                        page.get_by_role("button", name="Like", exact=True).click()
                        expect(
                            page.get_by_role("heading", name="Vegetables", exact=True)
                        ).to_be_visible()
                        page.reload()
                        page.get_by_role("button", name="Recipe ideas", exact=False).click()
                        expect(
                            page.get_by_role("heading", name="Vegetables", exact=True)
                        ).to_be_visible()
                        for current, following in (
                            ("Vegetables", "Chicken"),
                            ("Chicken", "Beef"),
                            ("Beef", "Fish"),
                            ("Fish", "Beans & lentils"),
                            ("Beans & lentils", "Cheese"),
                            ("Cheese", "Mushrooms"),
                        ):
                            expect(
                                page.get_by_role("heading", name=current, exact=True)
                            ).to_be_visible()
                            page.get_by_role("button", name="Skip this food", exact=True).click()
                            expect(
                                page.get_by_role("heading", name=following, exact=True)
                            ).to_be_visible()
                        page.get_by_role("button", name="Not for me", exact=True).click()
                        page.set_viewport_size({"width": 320, "height": 740})
                        capture("taste-narrow.png")
                        for current in ("Spicy food", "Mediterranean food", "Asian-inspired food"):
                            expect(
                                page.get_by_role("heading", name=current, exact=True)
                            ).to_be_visible()
                            page.get_by_role("button", name="Skip this food", exact=True).click()
                        expect(
                            page.get_by_role(
                                "heading", name="Your taste, ready to cook", exact=True
                            )
                        ).to_be_visible()
                        page.set_viewport_size({"width": 1440, "height": 1000})
                        capture("taste-summary-desktop.png")
                        context.set_offline(engine == "chromium")
                        page.get_by_role("button", name="Save my taste", exact=True).click()
                        expect(
                            page.get_by_label("What do you have at home?", exact=True)
                        ).to_be_visible()
                        assert calls == []
                        context.set_offline(False)
                        page.get_by_label("What do you have at home?", exact=True).fill(
                            "Pasta and tomatoes"
                        )
                        page.get_by_role("checkbox").check()
                        page.get_by_role("button", name="Give me three ideas", exact=True).click()
                        expect(
                            page.get_by_role("heading", name="Pasta one", exact=True)
                        ).to_be_visible(timeout=20000)
                        assert calls[0]["preferences"] == {
                            "liked_foods": ["Pasta", "Rice"],
                            "disliked_foods": ["Mushrooms"],
                        }, calls
                        assert operator.get("/api/v1/recipes").json()["items"] == []
                        profile = operator.get("/api/v1/household/food-profile").json()["profile"]
                        assert profile["taste_setup_done"] and profile["likes"] == ["pasta", "rice"]
                        page.set_viewport_size({"width": 1440, "height": 1000})
                        capture("ideas-desktop.png")
                        navigate(page, "Recipes")
                        page.get_by_role("button", name="Import recipe", exact=True).first.click()
                        expect(
                            page.get_by_text("Preparing this preview may send", exact=False)
                        ).to_be_visible()
                        assert page.get_by_label("Use configured AI", exact=True).count() == 0
                        assert (
                            page.get_by_label("I agree to send this content", exact=False).count()
                            == 0
                        )
                        capture("import-desktop.png")
                        page.set_viewport_size({"width": 390, "height": 844})
                        capture("import-mobile.png")
                        navigate(page, "Settings")
                        settings_section(page, "Your household")
                        page.get_by_label("Language", exact=True).select_option("de")
                        for theme, width in (("After Dark", 390), ("Sunday", 320)):
                            navigate(page, "Einstellungen")
                            settings_section(page, "Design-Bibliothek")
                            page.get_by_role("radio", name=theme, exact=True).check()
                            navigate(page, "Vorrat")
                            page.get_by_role(
                                "button", name="Vorrats-Basics wählen", exact=True
                            ).click()
                            page.set_viewport_size({"width": width, "height": 844})
                            capture("pantry-de-" + theme.lower().replace(" ", "-") + ".png")
                            page.get_by_role("button", name="Zurück", exact=True).click()
                            navigate(page, "Rezepte")
                            page.get_by_role("button", name="Rezeptideen", exact=False).click()
                            page.get_by_role("button", name="Dein Geschmack", exact=True).click()
                            capture("taste-de-" + theme.lower().replace(" ", "-") + ".png")
                        assert not errors, errors
                        browser.close()
            finally:
                server.should_exit = True
                thread.join(timeout=10)
    print(
        f"PASS ({engine}): pantry selection, gesture+button taste draft resume, explicit preference-aware ideas, clean imports; offline reload on Chromium only; synthetic provider only"
    )


if __name__ == "__main__":
    main()
