"""Real PWA/API/queue vision import with explicit synthetic provider HTTP responses."""

import io
import json
import os
import shutil
import socket
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import uvicorn
from PIL import Image
from playwright.sync_api import expect, sync_playwright

import aircooker.app as application
from aircooker.ai import provider_for


def main():
    fixture = json.loads(
        Path("contracts/recipe-import/examples/extraction-result.json").read_text()
    )
    calls = []

    def respond(request):
        body = json.loads(request.content)
        calls.append(body)
        raw = json.dumps(fixture)
        if "/models/" in request.url.path:
            assert body["contents"][0]["parts"][1]["inline_data"]["mime_type"] == "image/jpeg"
            return httpx.Response(
                200,
                json={
                    "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": raw}]}}]
                },
            )
        assert body["model"] == "synthetic/document-model"
        assert body["messages"][1]["content"][1]["type"] == "file"
        return httpx.Response(
            200, json={"choices": [{"finish_reason": "stop", "message": {"content": raw}}]}
        )

    application.provider_for = lambda config: provider_for(config, httpx.MockTransport(respond))
    captures = Path(os.environ.get("AIRCOOKER_SCREENSHOT_DIR", "build/ai-import-browser"))
    captures.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="mealf-ai-browser-") as temporary:
        root = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        os.environ["LOG_SETUP_TOKEN"] = "false"
        app = application.create_app(root)
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
            else:
                raise RuntimeError("AI import browser backend did not start")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=os.environ.get("CHROMIUM_EXECUTABLE")
                    or shutil.which("chromium")
                    or shutil.which("google-chrome"),
                    args=["--no-sandbox"],
                )
                context = browser.new_context(viewport={"width": 390, "height": 844})
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                axe = Path("frontend/node_modules/axe-core/axe.min.js").read_text()

                def audit():
                    page.evaluate(axe)
                    violations = page.evaluate(
                        "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))"
                    )
                    assert violations == [], violations
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")

                def rows():
                    return page.evaluate(
                        "async()=> (await(await fetch('/api/v1/recipes',{headers:{'X-Aircooker-Client':'pwa'}})).json()).items"
                    )

                def navigate(name):
                    page.get_by_role("navigation").get_by_role(
                        "button", name=name, exact=True
                    ).click()

                def configure(provider, model, key):
                    navigate("Settings")
                    form = page.locator(".ai-settings-form")
                    form.get_by_label("Enable AI extraction", exact=True).check()
                    form.get_by_label("AI provider", exact=True).select_option(provider)
                    form.get_by_label("Model name", exact=True).fill(model)
                    form.get_by_label("API key", exact=True).fill(key)
                    form.get_by_label("Images and screenshots", exact=True).check()
                    form.get_by_label("PDF documents", exact=True).check()
                    form.get_by_role("button", name="Save as default", exact=True).click()
                    expect(
                        page.get_by_text(
                            "AI settings saved. New imports use this provider and model.",
                            exact=True,
                        )
                    ).to_be_visible()
                    expect(form.get_by_label("API key", exact=True)).to_have_value("")
                    assert key not in page.evaluate(
                        "async()=> await(await fetch('/api/v1/admin/ai/providers',{headers:{'X-Aircooker-Client':'pwa'}})).text()"
                    )
                    audit()

                def upload(name, mime, raw):
                    navigate("Recipes")
                    page.get_by_role("button", name="Import recipe", exact=True).first.click()
                    page.get_by_role("button", name="Link or text", exact=True).click()
                    page.get_by_label("Image, PDF or cooking video", exact=False).set_input_files(
                        {"name": name, "mimeType": mime, "buffer": raw}
                    )
                    page.get_by_label("I agree to send this content", exact=False).check()
                    audit()
                    page.get_by_role("button", name="Prepare preview", exact=True).click()
                    page.get_by_role("button", name="Review", exact=True).last.click(timeout=20000)
                    expect(
                        page.get_by_role("heading", name="Review your import", exact=True)
                    ).to_be_visible()

                page.goto(base + "/app/")
                page.get_by_role("button", name="Open your kitchen", exact=True).click()
                page.get_by_label("Username", exact=True).fill("cook")
                page.get_by_label("Password", exact=True).fill("synthetic AI import password")
                page.get_by_label("One-time setup token", exact=True).fill(
                    (root / "config/setup-token").read_text()
                )
                page.get_by_label("Kitchen name", exact=True).fill("Synthetic vision kitchen")
                page.get_by_label("Household time zone", exact=True).fill("Europe/Zurich")
                page.get_by_role("button", name="Set up your kitchen", exact=True).click()
                expect(page.get_by_role("heading", name="Your kitchen", exact=True)).to_be_visible(
                    timeout=15000
                )
                configure("gemini", "synthetic-vision-model", "synthetic-browser-gemini-key")
                page.screenshot(path=str(captures / "settings-phone.png"), full_page=True)
                image = io.BytesIO()
                Image.new("RGB", (80, 80), "white").save(image, format="PNG")
                upload("synthetic-scan.png", "image/png", image.getvalue())
                assert rows() == []
                expect(page.get_by_label("Preparation time (minutes)", exact=True)).to_have_value(
                    "10"
                )
                page.get_by_label("Recipe name", exact=True).fill("Reviewed vision pasta")
                page.get_by_label("Preparation time (minutes)", exact=True).fill("12")
                page.get_by_label("Servings", exact=True).fill("3")
                audit()
                page.screenshot(path=str(captures / "review-phone.png"), full_page=True)
                page.get_by_role("button", name="Save", exact=True).click()
                deadline = time.monotonic() + 20
                stored_rows = []
                while time.monotonic() < deadline:
                    stored_rows = rows()
                    if len(stored_rows) == 1:
                        break
                    page.wait_for_timeout(200)
                assert len(stored_rows) == 1, "Reviewed recipe was not committed"
                stored = stored_rows[0]["payload"]
                assert (
                    stored["title"] == "Reviewed vision pasta"
                    and stored["times"]["prep_minutes"] == 12
                )
                assert (
                    stored["servings"] == "3"
                    and stored["ingredients"][0]["quantity_text"] == "200 g"
                )
                configure("openrouter", "synthetic/document-model", "synthetic-browser-router-key")
                upload(
                    "synthetic.pdf", "application/pdf", b"%PDF-1.4\nSynthetic test source\n%%EOF"
                )
                assert len(rows()) == 1  # A preview has not saved another recipe.
                assert len(calls) == 2 and not errors, errors
                context.close()
                browser.close()
                print(
                    "PASS: real PWA settings/provider switch, Gemini image OCR draft, OpenRouter PDF draft, editable timings/servings, explicit confirmation, key redaction, phone layout and Axe; provider HTTP responses are synthetic."
                )
        finally:
            server.should_exit = True
            thread.join(timeout=10)


if __name__ == "__main__":
    main()
