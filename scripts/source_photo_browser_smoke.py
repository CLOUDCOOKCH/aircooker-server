"""Real PWA/SQLite/worker photo review and cached fallbacks; explicit source/AI doubles."""

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

from mealf.app import create_app
from mealf.importing import FetchedPage
from mealf.recipe_extraction import ExtractionResult
from mealf.source_images import source_photo


def main():
    fixture = json.loads(
        Path("contracts/recipe-import/examples/extraction-result.json").read_text()
    )
    fixture["recipe"]["title"] = "Synthetic source lemon recipe"
    fixture["recipe"]["servings"] = None
    source = "https://source.example.invalid/recipes/lemon/"
    page_data = FetchedPage('<meta property="og:image" content="dish.png">', source)
    artwork = Path("frontend/public/art/lemon-chicken.png").read_bytes()
    calls = []

    class Provider:
        def extract(self, value):
            assert value.text == page_data.text
            calls.append("ai")
            return ExtractionResult.model_validate(fixture)

        def close(self):
            pass

    captures = Path(os.environ.get("MEALF_SCREENSHOT_DIR", "build/source-photo-browser"))
    captures.mkdir(parents=True, exist_ok=True)
    with (
        TemporaryDirectory(prefix="mealf-source-photo-") as directory,
        patch("mealf.app.bounded_fetch_page", lambda url: page_data),
        patch("mealf.app.bounded_source_photo", source_photo),
        patch(
            "mealf.source_images.fetch_resource",
            lambda url, *args: (artwork, "image/png", url),
        ),
        patch("mealf.app.provider_for", lambda config: Provider()),
    ):
        root = Path(directory)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        os.environ["LOG_SETUP_TOKEN"] = "false"
        app = create_app(root)
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
            with (
                sync_playwright() as playwright,
                httpx.Client(base_url=base, trust_env=False, timeout=15) as operator,
            ):
                browser = playwright.chromium.launch(
                    executable_path=os.environ.get("CHROMIUM_EXECUTABLE")
                    or shutil.which("chromium")
                    or shutil.which("google-chrome"),
                    args=["--no-sandbox"],
                )
                context = browser.new_context(viewport={"width": 1440, "height": 1000})
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base + "/app/")
                page.get_by_role("button", name="Open your kitchen", exact=True).click()
                page.get_by_label("Username", exact=True).fill("cook")
                page.get_by_label("Password", exact=True).fill("synthetic source-photo password")
                page.get_by_label("One-time setup token", exact=True).fill(
                    (root / "config/setup-token").read_text()
                )
                page.get_by_label("Kitchen name", exact=True).fill("Synthetic photo kitchen")
                page.get_by_label("Household time zone", exact=True).fill("Europe/Zurich")
                page.get_by_role("button", name="Set up your kitchen", exact=True).click()
                expect(page.get_by_role("heading", name="Your kitchen", exact=True)).to_be_visible(
                    timeout=15000
                )
                device = str(uuid4())
                login = operator.post(
                    "/api/v1/auth/login",
                    json={
                        "username": "cook",
                        "password": "synthetic source-photo password",
                        "device_id": device,
                    },
                )
                login.raise_for_status()
                operator.headers["Authorization"] = "Bearer " + login.json()["access_token"]
                operator.put(
                    "/api/v1/admin/ai",
                    json={
                        "provider": "gemini",
                        "model": "synthetic-text-model",
                        "api_key": "synthetic-key",
                        "input_formats": ["text"],
                    },
                ).raise_for_status()
                broken_id = str(uuid4())
                operator.put(
                    "/api/v1/media/" + broken_id,
                    files={"file": ("synthetic.png", artwork, "image/png")},
                ).raise_for_status()
                page.route(
                    "**/api/v1/media/" + broken_id,
                    lambda route: route.fulfill(
                        status=200, content_type="image/jpeg", body=b"invalid-image-fixture"
                    ),
                )
                for title, photo in [
                    ("Sunday tomato soup", None),
                    ("Saved recipe with unreadable photo", broken_id),
                ]:
                    mid = str(uuid4())
                    operator.post(
                        "/api/v1/sync/push",
                        json={
                            "mutations": [
                                {
                                    "mutation_id": mid,
                                    "idempotency_key": mid,
                                    "device_id": device,
                                    "entity_id": str(uuid4()),
                                    "kind": "recipe",
                                    "operation": "upsert",
                                    "base_revision": 0,
                                    "client_timestamp": "2000-01-01T00:00:00Z",
                                    "payload": {
                                        "title": title,
                                        "servings": "2",
                                        "ingredients": [
                                            {
                                                "id": str(uuid4()),
                                                "name": "tomatoes",
                                                "quantity": "200",
                                                "unit": "g",
                                            }
                                        ],
                                        "steps": ["Cook slowly."],
                                        "image_id": photo,
                                    },
                                }
                            ]
                        },
                    ).raise_for_status()
                page.reload()
                navigate(page, "Recipes")
                expect(page.locator(".recipe-card")).to_have_count(2, timeout=15000)
                expect(page.locator(".recipe-card .photo-placeholder")).to_have_count(2)

                def audit():
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                    assert not page.evaluate(
                        "async()=> (await axe.run(document.querySelector('main'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                    )

                def capture(name):
                    page.evaluate(
                        "async()=>{for(const image of document.images)await image.decode().catch(()=>{});}"
                    )
                    page.evaluate("scrollTo(0,0)")
                    page.screenshot(
                        path=str(captures / name), full_page=True, animations="disabled"
                    )

                audit()
                capture("recipe-fallback-desktop.png")
                page.get_by_role("button", name="Sunday tomato soup", exact=False).click()
                expect(page.locator(".detail-photo.photo-placeholder")).to_be_visible()
                audit()
                capture("recipe-fallback-detail-desktop.png")
                page.get_by_role("button", name="Back", exact=True).click()
                page.get_by_role("button", name="Import recipe", exact=True).first.click()
                page.get_by_label("Recipe URL", exact=True).fill(source)
                page.get_by_label("Use configured AI", exact=True).check()
                page.get_by_label("I agree to send this content", exact=False).check()
                page.get_by_role("button", name="Prepare preview", exact=True).click()
                page.get_by_role("button", name="Review", exact=True).last.click(timeout=20000)
                expect(page.locator(".editor-photo.food-photo")).to_be_visible()
                assert len(operator.get("/api/v1/recipes").json()["items"]) == 2
                page.get_by_label("Recipe name", exact=True).fill("Reviewed source lemon recipe")
                audit()
                capture("source-image-review-desktop.png")
                page.get_by_label("Servings", exact=True).fill("2")
                page.get_by_role("button", name="Save", exact=True).click()
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    rows = operator.get("/api/v1/recipes").json()["items"]
                    if len(rows) == 3:
                        break
                    page.wait_for_timeout(200)
                assert len(rows) == 3 and calls == ["ai"]
                imported = next(
                    r for r in rows if r["payload"]["title"] == "Reviewed source lemon recipe"
                )
                assert imported["payload"]["provenance"]["image_source"] == source + "dish.png"
                navigate(page, "Settings")
                settings_section(page, "Your household")
                page.get_by_label("Language", exact=True).select_option("de")
                page.evaluate("window.mealfAppearance.set('after-dark')")
                page.set_viewport_size({"width": 390, "height": 844})
                navigate(page, "Rezepte")
                expect(page.locator(".recipe-card")).to_have_count(3)
                expect(page.locator(".recipe-card .food-photo")).to_have_count(1)
                audit()
                capture("recipe-photos-phone-de-dark.png")
                page.evaluate("async()=>{await navigator.serviceWorker.ready}")
                context.set_offline(True)
                page.reload()
                navigate(page, "Rezepte")
                expect(page.locator(".recipe-card .food-photo")).to_have_count(1)
                expect(page.locator(".recipe-card .photo-placeholder")).to_have_count(2)
                audit()
                capture("recipe-photos-offline-phone-de-dark.png")
                assert not errors, errors
                context.close()
                browser.close()
                print(
                    "PASS: real PWA/worker AI-source image review, explicit save, original attribution, missing/broken-photo peach fallbacks, EN desktop/DE dark phone/Axe and cached offline reload. External source/AI responses are synthetic; no physical iPhone or live provider proof."
                )
        finally:
            server.should_exit = True
            thread.join(timeout=10)


if __name__ == "__main__":
    main()
