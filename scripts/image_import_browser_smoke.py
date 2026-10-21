"""Real image chooser, local OCR and reviewed offline recipe import; synthetic account.

Camera checks cover native capture/chooser semantics, not physical camera hardware.
WebKit network-loss testing stops the real backend; no worker/storage doubles.
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
    captures = (
        Path(os.environ.get("AIRCOOKER_SCREENSHOT_DIR", "build/image-import-browser")) / engine
    )
    captures.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="mealf-image-browser-") as temporary:
        root = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        tls_root = os.environ.get("MEALF_BROWSER_TEST_TLS")
        if engine == "webkit" and not tls_root:
            raise RuntimeError("WebKit authenticated flow requires a trusted HTTPS test fixture")
        base = f"{'https' if tls_root else 'http'}://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base

        def start_backend():
            app = create_app(root, run_worker=True)
            server = uvicorn.Server(
                uvicorn.Config(
                    app,
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
            for _ in range(100):
                if server.started:
                    return app, server, thread
                time.sleep(0.05)
            raise RuntimeError("Image import backend not ready")

        app, server, thread = start_backend()
        try:
            with sync_playwright() as playwright:
                options = {}
                if engine == "chromium":
                    options = {
                        "executable_path": os.environ.get("CHROMIUM_EXECUTABLE")
                        or shutil.which("chromium")
                        or shutil.which("google-chrome"),
                        "args": ["--no-sandbox"],
                    }
                context = getattr(playwright, engine).launch_persistent_context(
                    str(root / "profile"), viewport={"width": 1440, "height": 1000}, **options
                )
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on(
                    "response",
                    lambda response: print(
                        f"Test API status: {response.status} {response.url.split('/api/v1/', 1)[1].split('?')[0]}"
                    )
                    if response.status >= 400 and "/api/v1/" in response.url
                    else None,
                )
                axe = Path("frontend/node_modules/axe-core/axe.min.js").read_text()

                def audit():
                    page.evaluate(axe)
                    violations = page.evaluate(
                        "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))"
                    )
                    assert violations == [], violations
                    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")

                def outage(offline):
                    nonlocal app, server, thread
                    if engine == "chromium":
                        context.set_offline(offline)
                    elif offline:
                        server.should_exit = True
                        thread.join(timeout=10)
                        assert not thread.is_alive()
                    else:
                        app, server, thread = start_backend()

                def import_page():
                    page.get_by_role("button", name="Import recipe", exact=True).click()
                    expect(
                        page.get_by_role("heading", name="Import recipe", exact=True)
                    ).to_be_visible()
                    page.get_by_role("button", name="Photo or screenshot", exact=True).click()

                def choose(button, fixture):
                    with page.expect_file_chooser() as chooser:
                        page.get_by_role("button", name=button, exact=True).click()
                    chooser.value.set_files(str(Path("tests/fixtures") / fixture))
                    expect(page.locator(".import-image-preview")).to_be_visible()

                def recipes():
                    return page.evaluate(
                        "async()=> (await (await fetch('/api/v1/recipes',{headers:{'X-Aircooker-Client':'pwa'}})).json()).items"
                    )

                page.goto(base + "/app/")
                page.get_by_role("button", name="Open your kitchen").click()
                page.get_by_label("Username", exact=True).fill("cook")
                page.get_by_label("Password", exact=True).fill(
                    "synthetic image browser kitchen password"
                )
                page.get_by_label("One-time setup token", exact=True).fill(
                    (root / "config/setup-token").read_text()
                )
                page.get_by_label("Kitchen name", exact=True).fill("Image test kitchen")
                page.get_by_label("Household time zone", exact=True).fill("Europe/Zurich")
                page.get_by_role("button", name="Set up your kitchen", exact=True).click()
                expect(page.get_by_role("heading", name="Your kitchen", exact=True)).to_be_visible(
                    timeout=15000
                )
                import_page()
                assert page.locator("input[capture]").get_attribute("capture") == "environment"
                choose("Choose image", "recipe-photo-en.png")
                audit()
                page.screenshot(path=str(captures / "image-chooser-desktop.png"))
                page.wait_for_function("!!navigator.serviceWorker.controller")
                outage(True)
                page.get_by_role("button", name="Prepare preview", exact=True).click()
                expect(page.locator(".import-job")).to_contain_text("Queued")
                expect(page.locator(".import-job img")).to_be_visible()
                page.reload()
                expect(page.get_by_role("heading", name="Your kitchen", exact=True)).to_be_visible()
                import_page()
                expect(page.locator(".import-job")).to_contain_text("Queued")
                expect(page.locator(".import-job img")).to_be_visible()
                outage(False)
                page.get_by_role("button", name="Sync now", exact=True).click()
                expect(page.locator(".import-job")).to_contain_text(
                    "Ready to review", timeout=45000
                )
                assert recipes() == [], "Import must not create a recipe before review"
                page.locator(".import-job").get_by_role("button", name="Review", exact=True).click()
                expect(page.get_by_role("heading", name="Review your import")).to_be_visible()
                expect(page.get_by_label("Recipe name", exact=True)).to_have_value("Lemon rice")
                expect(page.locator(".editor-photo")).to_be_visible()
                page.get_by_text("Recognized text", exact=True).click()
                expect(page.locator(".import-source-text")).to_contain_text("200 g rice")
                page.get_by_label("Recipe name", exact=True).fill("Reviewed photo rice")
                audit()
                page.screenshot(path=str(captures / "image-review-desktop.png"))
                outage(True)
                page.get_by_role("button", name="Save", exact=True).click()
                page.get_by_role("navigation").get_by_role(
                    "button", name="Recipes", exact=True
                ).click()
                expect(
                    page.get_by_role("button", name="Reviewed photo rice", exact=False).first
                ).to_be_visible()
                page.reload()
                page.get_by_role("navigation").get_by_role(
                    "button", name="Recipes", exact=True
                ).click()
                expect(
                    page.get_by_role("button", name="Reviewed photo rice", exact=False).first
                ).to_be_visible()
                outage(False)
                page.get_by_role("button", name="Sync now", exact=True).click()
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    stored = recipes()
                    if len(stored) == 1:
                        break
                    page.wait_for_timeout(200)
                assert len(stored) == 1 and stored[0]["payload"]["title"] == "Reviewed photo rice"
                assert stored[0]["payload"]["image_id"]
                page.get_by_role("navigation").get_by_role("button", name="Settings").click()
                page.get_by_role("radio", name="After Dark", exact=True).evaluate(
                    "e=>e.scrollIntoView({block:'center',behavior:'instant'})"
                )
                page.get_by_role("radio", name="After Dark", exact=True).check()
                page.get_by_label("Language", exact=True).select_option("de")
                page.set_viewport_size({"width": 390, "height": 844})
                page.get_by_role("navigation").get_by_role(
                    "button", name="Start", exact=True
                ).click()
                page.get_by_role("button", name="Rezept importieren", exact=True).click()
                page.get_by_role("button", name="Foto oder Screenshot", exact=True).click()
                choose("Foto aufnehmen", "recipe-photo-de.png")
                audit()
                page.screenshot(path=str(captures / "image-camera-phone-de-dark.png"))
                page.set_viewport_size({"width": 320, "height": 568})
                audit()
                page.get_by_role("button", name="Vorschau vorbereiten", exact=True).click()
                expect(page.locator(".import-job").filter(has_text="Tomatenreis")).to_contain_text(
                    "Bereit zur Prüfung", timeout=45000
                )
                german = page.locator(".import-job").filter(has_text="Tomatenreis")
                german.get_by_role("button", name="Prüfen", exact=True).click()
                expect(page.get_by_label("Rezeptname", exact=True)).to_have_value("Tomatenreis")
                page.set_viewport_size({"width": 390, "height": 844})
                audit()
                page.screenshot(path=str(captures / "image-review-phone-de-dark.png"))
                # Two extraction jobs were delivered, only one explicitly saved recipe exists.
                assert len(recipes()) == 1
                assert errors == [], errors
                context.close()
            (captures / "evidence.json").write_text(
                json.dumps(
                    {
                        "engine": engine,
                        "backend": "real",
                        "ocr": "real Tesseract eng+deu",
                        "transport": "trusted HTTPS" if tls_root else "HTTP loopback Chromium",
                        "offline": "browser offline flag"
                        if engine == "chromium"
                        else "actual backend outage",
                        "images": "synthetic EN/DE fixtures",
                        "saved_only_after_review": True,
                        "offline_image_and_edit_reload": True,
                        "camera": "capture and native chooser; no physical camera verification",
                        "axe": "desktop EN/light, phone DE/dark and 320px",
                    },
                    indent=2,
                )
                + "\n"
            )
            print(
                f"PASS: {engine} native image chooser/capture, real local EN/DE OCR, offline image/edit reload, explicit review/save, metadata-safe upload and contrast/Axe"
            )
        finally:
            server.should_exit = True
            thread.join(timeout=10)


if __name__ == "__main__":
    main()
