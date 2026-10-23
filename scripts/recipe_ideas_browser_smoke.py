"""Real PWA/SQLite/jobs/offline review; provider HTTP only is an explicit double."""

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
from browser_settings import settings_section
from playwright.sync_api import expect, sync_playwright

from mealf.ai import provider_for
from mealf.app import create_app


def main():
    captures = Path(os.environ.get("MEALF_IDEAS_SCREENSHOT_DIR", "build/recipe-ideas-browser"))
    captures.mkdir(parents=True, exist_ok=True)
    calls = []
    broken = False
    failure_status = 200

    def transport(request):
        body = json.loads(request.content)
        system = body["system_instruction"]["parts"][0]["text"]
        assert "creative generation" in system and "tools" not in body
        source = json.loads(json.loads(body["contents"][0]["parts"][0]["text"])["untrusted_source"])
        calls.append(source)
        if failure_status != 200:
            return httpx.Response(
                failure_status, json={"error": {"message": "private-provider-content"}}
            )
        titles = (
            ["Spaghetti bolognese", "Beef pasta bake", "Spiced beef noodles"]
            if source["language"] == "en"
            else ["Kürbissuppe", "Pilzrisotto", "Ofengemüse"]
        )
        ingredients = [
            {"name": "Spaghetti", "quantity": "200", "unit": "g"},
            {"name": "Minced beef", "quantity": "250", "unit": "g"},
            {"name": "Tomatoes", "quantity": "400", "unit": "g"},
        ]
        ideas = {
            "ideas": [
                {
                    "title": title,
                    "description": "A synthetic AI proposal for browser acceptance."
                    if source["language"] == "en"
                    else "Ein synthetischer KI-Vorschlag für den Browsertest.",
                    "servings": "2",
                    "ingredients": ingredients,
                    "steps": ["Cook ingredients thoroughly.", "Combine and serve."],
                }
                for title in titles
            ]
        }
        if broken:
            ideas = {"ideas": []}
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(ideas)}]}}
                ]
            },
        )

    with TemporaryDirectory(prefix="mealf-ideas-browser-") as directory:
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
            app = create_app(root)
            server = uvicorn.Server(
                uvicorn.Config(
                    app, host="127.0.0.1", port=port, log_level="error", access_log=False
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
                    auth = operator.post(
                        "/api/v1/setup",
                        headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
                        json={
                            "name": "Synthetic ideas kitchen",
                            "username": "cook",
                            "password": "synthetic ideas password",
                            "timezone": "Europe/Zurich",
                            "device_id": str(uuid4()),
                        },
                    )
                    auth.raise_for_status()
                    operator.headers["Authorization"] = "Bearer " + auth.json()["access_token"]
                    configured = operator.put(
                        "/api/v1/admin/ai",
                        json={
                            "provider": "gemini",
                            "model": "synthetic-model",
                            "api_key": "synthetic-only",
                            "input_formats": ["text"],
                        },
                    )
                    configured.raise_for_status()
                    with sync_playwright() as p:
                        browser = p.chromium.launch(
                            executable_path=shutil.which("chromium")
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
                        page.get_by_label("Password", exact=True).fill("synthetic ideas password")
                        page.get_by_role("button", name="Sign in", exact=True).click()
                        page.get_by_role("button", name="Recipe ideas", exact=False).click()
                        page.get_by_label("What do you have at home?", exact=True).fill(
                            "Spaghetti and minced beef"
                        )
                        generate = page.get_by_role(
                            "button", name="Give me three ideas", exact=True
                        )
                        expect(generate).to_be_disabled()
                        page.screenshot(
                            path=str(captures / "ideas-input-desktop.png"), full_page=True
                        )
                        page.get_by_role("checkbox").check()
                        generate.click()
                        expect(
                            page.get_by_role("heading", name="Spaghetti bolognese", exact=True)
                        ).to_be_visible(timeout=20000)
                        assert (
                            len(calls) == 1
                            and calls[0]["available_ingredients"] == "Spaghetti and minced beef"
                        )
                        assert operator.get("/api/v1/recipes").json()["items"] == []
                        page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                        assert not page.evaluate(
                            "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                        )
                        page.screenshot(
                            path=str(captures / "ideas-ready-desktop.png"), full_page=True
                        )
                        page.get_by_role("button", name="Review recipe", exact=True).first.click()
                        expect(page.get_by_label("Recipe name", exact=True)).to_have_value(
                            "Spaghetti bolognese"
                        )
                        page.get_by_label("Recipe name", exact=True).fill("Reviewed bolognese")
                        page.wait_for_function("!!navigator.serviceWorker.controller")
                        context.set_offline(True)
                        page.get_by_role("button", name="Save", exact=True).click()
                        expect(
                            page.get_by_role("button", name="Reviewed bolognese", exact=False)
                        ).to_be_visible()
                        page.reload()
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Recipes", exact=True
                        ).click()
                        expect(
                            page.get_by_role("button", name="Reviewed bolognese", exact=False)
                        ).to_be_visible()
                        context.set_offline(False)
                        page.get_by_role("button", name="Sync now", exact=True).click()
                        for _ in range(50):
                            saved = operator.get("/api/v1/recipes").json()["items"]
                            if saved:
                                break
                            page.wait_for_timeout(100)
                        assert (
                            len(saved) == 1
                            and saved[0]["payload"]["provenance"]["extractor"]
                            == "ai-generated-ideas"
                        )
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Settings", exact=True
                        ).click()
                        settings_section(page, "Your household")
                        page.get_by_label("Language", exact=True).select_option("de")
                        page.evaluate("window.mealfAppearance.set('after-dark')")
                        page.set_viewport_size({"width": 390, "height": 844})
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Rezepte", exact=True
                        ).click()
                        page.get_by_role("button", name="Rezeptideen", exact=False).click()
                        page.get_by_role("radio", name="Überrasch mich", exact=True).check()
                        page.get_by_role("checkbox").check()
                        page.get_by_role("button", name="Gib mir drei Ideen", exact=True).click()
                        expect(
                            page.get_by_role("heading", name="Kürbissuppe", exact=True)
                        ).to_be_visible(timeout=20000)
                        assert (
                            len(calls) == 2
                            and calls[-1]["available_ingredients"] == ""
                            and calls[-1]["mode"] == "surprise"
                        )
                        page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                        assert not page.evaluate(
                            "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                        )
                        page.screenshot(
                            path=str(captures / "ideas-surprise-phone-de-dark.png"), full_page=True
                        )
                        page.set_viewport_size({"width": 320, "height": 740})
                        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                        page.screenshot(
                            path=str(captures / "ideas-surprise-phone-320-de-dark.png"),
                            full_page=True,
                        )
                        page.set_viewport_size({"width": 390, "height": 844})
                        context.set_offline(True)
                        page.reload()
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Rezepte", exact=True
                        ).click()
                        page.get_by_role("button", name="Rezeptideen", exact=False).click()
                        expect(
                            page.get_by_role("heading", name="Kürbissuppe", exact=True)
                        ).to_be_visible()
                        expect(
                            page.get_by_role("button", name="Gib mir drei Ideen", exact=True)
                        ).to_be_disabled()
                        page.screenshot(
                            path=str(captures / "ideas-offline-phone-de-dark.png"), full_page=True
                        )
                        context.set_offline(False)
                        page.reload()
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Rezepte", exact=True
                        ).click()
                        page.get_by_role("button", name="Rezeptideen", exact=False).click()
                        broken = True
                        page.get_by_role("checkbox").check()
                        page.get_by_role("button", name="Gib mir drei Ideen", exact=True).click()
                        expect(page.get_by_role("alert")).to_be_visible(timeout=20000)
                        expect(page.get_by_role("alert")).to_contain_text(
                            "ai_schema_validation_failed"
                        )
                        expect(page.get_by_role("alert")).to_contain_text(
                            "keine drei gültigen Rezepte"
                        )
                        broken = False
                        for failure_status, code, explanation in [
                            (404, "ai_model_or_endpoint_not_found", "API-Modell-ID"),
                            (429, "ai_rate_limited", "Kontingentlimit"),
                        ]:
                            page.get_by_role(
                                "button", name="Gib mir drei Ideen", exact=True
                            ).click()
                            expect(page.get_by_role("alert")).to_contain_text(code, timeout=20000)
                            expect(page.get_by_role("alert")).to_contain_text(explanation)
                            assert "private-provider-content" not in page.content()
                            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                            page.screenshot(
                                path=str(captures / f"ideas-error-{failure_status}-phone-de.png"),
                                full_page=True,
                            )
                        call_count = len(calls)
                        page.reload()
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Rezepte", exact=True
                        ).click()
                        page.get_by_role("button", name="Rezeptideen", exact=False).click()
                        expect(page.get_by_role("alert")).to_contain_text("ai_rate_limited")
                        assert len(calls) == call_count
                        page.set_viewport_size({"width": 1440, "height": 1000})
                        page.screenshot(
                            path=str(captures / "ideas-error-429-desktop-de.png"), full_page=True
                        )
                        page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                        assert not page.evaluate(
                            "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                        )
                        page.get_by_role("button", name="Einstellungen öffnen", exact=True).click()
                        settings_section(page, "KI-Rezeptimport")
                        expect(page.get_by_label("Modellname", exact=True)).to_be_visible()
                        model_field = page.get_by_label("Modellname", exact=True)
                        model_field.fill("Gemini 3.8 Flash")
                        assert not model_field.evaluate("input => input.checkValidity()")
                        model_field.fill("gemini-3.8-flash")
                        assert model_field.evaluate("input => input.checkValidity()")
                        assert len(operator.get("/api/v1/recipes").json()["items"]) == 1
                        # Simulate an installed preview's old, now-invalid cached proposal.
                        cached = page.evaluate("""async () => {
                            const name = (await indexedDB.databases()).find(d => d.name.startsWith('mealf:')).name;
                            const db = await new Promise((resolve, reject) => {
                                const r = indexedDB.open(name); r.onsuccess = () => resolve(r.result); r.onerror = reject;
                            });
                            const tx = db.transaction('meta', 'readwrite'), store = tx.objectStore('meta');
                            const draft = await new Promise(resolve => { const r = store.get('recipe-ideas:v1'); r.onsuccess = () => resolve(r.result); });
                            draft.job = {id: draft.request.request_id, state:'ready', recipes:[{title:'Legacy proposal', servings:'1e-1000000'}]};
                            store.put(draft, 'recipe-ideas:v1');
                            await new Promise((resolve, reject) => {tx.oncomplete=resolve;tx.onerror=reject;});
                            db.close(); return {name, draft};
                        }""")
                        call_count = len(calls)
                        page.reload()
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Rezepte", exact=True
                        ).click()
                        page.get_by_role("button", name="Rezeptideen", exact=False).click()
                        expect(page.get_by_role("alert")).to_be_visible()
                        # An ordinary edit must not overwrite the rejected cached request.
                        page.get_by_role("textbox").fill("Keep the old proposal")
                        retained = page.evaluate(
                            """async name => {
                            const db = await new Promise(resolve => {const r=indexedDB.open(name);r.onsuccess=()=>resolve(r.result);});
                            const value = await new Promise(resolve => {const r=db.transaction('meta').objectStore('meta').get('recipe-ideas:v1');r.onsuccess=()=>resolve(r.result);});
                            db.close();return value;
                        }""",
                            cached["name"],
                        )
                        assert retained == cached["draft"] and len(calls) == call_count
                        legacy_leftover = str(uuid4())
                        recipe_id = operator.get("/api/v1/recipes").json()["items"][0]["id"]
                        page.evaluate(
                            """async ({name, id, recipe}) => {
                            const db = await new Promise(resolve => {const r=indexedDB.open(name);r.onsuccess=()=>resolve(r.result);});
                            const tx=db.transaction('entities','readwrite');
                            tx.objectStore('entities').put({key:'leftover:'+id,id,kind:'leftover',revision:0,deleted:false,payload:{recipe_id:recipe,portions:'1e-1000000',produced_on:'2026-10-19',discarded:false}});
                            await new Promise((resolve,reject)=>{tx.oncomplete=resolve;tx.onerror=reject;});db.close();
                        }""",
                            {"name": cached["name"], "id": legacy_leftover, "recipe": recipe_id},
                        )
                        page.reload()
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Kalender", exact=True
                        ).click()
                        expect(
                            page.locator(".leftovers-section").get_by_role("alert")
                        ).to_be_visible()
                        assert not errors, errors
                        browser.close()
            finally:
                server.should_exit = True
                thread.join(timeout=20)
                assert not thread.is_alive()
    print(
        "PASS: actual AI adapters over synthetic provider HTTP, durable job/three-idea previews, ingredient and surprise privacy, no automatic save, offline edited Save/reload/sync, cached ideas, malformed-output/model/quota errors, no paid retry on reload, settings recovery and Gemini model-ID validation, rejected legacy proposal retained without retry/overwrite, EN desktop/DE320 phone and Axe; no live provider/iPhone verification."
    )


if __name__ == "__main__":
    main()
