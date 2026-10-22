"""Real PWA/SQLite/helper callback; OpenAI identity and inference use explicit doubles."""

import json
import os
import shutil
import socket
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlencode, urlsplit
from uuid import uuid4

import httpx
import jwt
import uvicorn
from browser_settings import settings_section
from cryptography.hazmat.primitives.asymmetric import rsa
from playwright.sync_api import expect, sync_playwright

from mealf.app import create_app
from mealf.chatgpt_helper import connect
from mealf.chatgpt_protocol import AUTHORIZE, DISCOVERY, ISSUER, JWKS, RESOURCE, SCOPES, TOKEN


def main():
    captures = Path(os.environ.get("MEALF_CHATGPT_CAPTURES", "build/chatgpt-browser"))
    captures.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client_id = "oaiapp_browser_synthetic"
    calls = []
    source = json.loads(Path("contracts/recipe-import/examples/extraction-result.json").read_text())

    def tokens(nonce):
        now = int(time.time())
        common = {"iss": ISSUER, "sub": "synthetic-browser-person", "iat": now, "exp": now + 3600}

        def sign(value):
            return jwt.encode(value, key, algorithm="RS256", headers={"kid": "synthetic-browser"})

        return {
            "access_token": sign(
                {**common, "aud": RESOURCE, "client_id": client_id, "scope": SCOPES}
            ),
            "id_token": sign(
                {**common, "aud": client_id, "nonce": nonce, "email": "synthetic@example.invalid"}
            ),
            "refresh_token": "synthetic-browser-refresh-secret",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": SCOPES,
        }

    def respond(request):
        calls.append(request)
        url = str(request.url)
        if url == DISCOVERY:
            return httpx.Response(
                200,
                json={
                    "issuer": ISSUER,
                    "authorization_endpoint": AUTHORIZE,
                    "token_endpoint": TOKEN,
                    "jwks_uri": JWKS,
                    "revocation_endpoint": ISSUER + "/revoke",
                },
            )
        if url == JWKS:
            public = jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key(), as_dict=True)
            return httpx.Response(
                200, json={"keys": [{**public, "alg": "RS256", "kid": "synthetic-browser"}]}
            )
        if url == RESOURCE + "/models":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "slug": "synthetic-text",
                            "display_name": "Synthetic text model",
                            "visibility": "list",
                        }
                    ]
                },
            )
        if url == ISSUER + "/revoke":
            return httpx.Response(503, json={"error": "synthetic revocation outage"})
        assert url == RESOURCE + "/responses"
        body = json.loads(request.content)
        assert (
            body["store"] is False and body["stream"] is True and body["model"] == "synthetic-text"
        )
        event = {
            "type": "response.completed",
            "response": {
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "status": "completed",
                        "content": [{"type": "output_text", "text": json.dumps(source)}],
                    }
                ],
            },
        }
        return httpx.Response(
            200,
            content="data: " + json.dumps(event) + "\n\n",
            headers={"Content-Type": "text/event-stream"},
        )

    with TemporaryDirectory(prefix="mealf-chatgpt-browser-") as temporary:
        root = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        os.environ["LOG_SETUP_TOKEN"] = "false"
        app = create_app(root)
        app.state.chatgpt.protocol.transport = httpx.MockTransport(respond)
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
                raise RuntimeError("Synthetic backend did not start")
            with httpx.Client(base_url=base, trust_env=False) as operator:
                setup = operator.post(
                    "/api/v1/setup",
                    headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
                    json={
                        "name": "Synthetic ChatGPT test kitchen",
                        "username": "cook",
                        "password": "synthetic browser password",
                        "timezone": "Europe/Zurich",
                        "device_id": str(uuid4()),
                    },
                )
                setup.raise_for_status()
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(
                        executable_path=os.environ.get("CHROMIUM_EXECUTABLE")
                        or shutil.which("chromium")
                        or shutil.which("google-chrome"),
                        args=["--no-sandbox"],
                    )
                    context = browser.new_context(viewport={"width": 1440, "height": 1000})
                    page = context.new_page()
                    page.set_default_timeout(15000)
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(base + "/app/")
                    page.get_by_role("button", name="Open your kitchen", exact=True).click()
                    page.get_by_label("Username", exact=True).fill("cook")
                    page.get_by_label("Password", exact=True).fill("synthetic browser password")
                    page.get_by_role("button", name="Sign in", exact=True).click()
                    expect(
                        page.get_by_role("heading", name="Your kitchen", exact=True)
                    ).to_be_visible(timeout=15000)
                    page.get_by_role("navigation").get_by_role(
                        "button", name="Settings", exact=True
                    ).click()
                    settings_section(page, "Your ChatGPT plan")
                    panel = page.locator(".chatgpt-settings")
                    expect(
                        panel.get_by_role("button", name="Connect ChatGPT", exact=True)
                    ).to_be_disabled()
                    panel.get_by_role("checkbox").check()
                    panel.get_by_role("button", name="Connect ChatGPT", exact=True).click()
                    pair_code = panel.get_by_label("One-use pairing code", exact=True).input_value()
                    expect(
                        panel.get_by_text(
                            "Waiting for your computer to finish sign-in…", exact=True
                        )
                    ).to_be_visible()
                    panel.screenshot(path=str(captures / "pairing-desktop.png"))
                    assert (
                        operator.get("/api/v1/integrations/chatgpt/helper").text
                        == Path("src/mealf/chatgpt_helper.py").read_text()
                    )
                    nonce = {}
                    callback_threads = []

                    def helper_request(url, body=None, *, form=False):
                        if url.startswith("https://mealf-helper.invalid/api/"):
                            response = operator.post(
                                url.removeprefix("https://mealf-helper.invalid"), json=body
                            )
                            response.raise_for_status()
                            return response.json()
                        if url == DISCOVERY:
                            return {
                                "issuer": ISSUER,
                                "authorization_endpoint": AUTHORIZE,
                                "token_endpoint": TOKEN,
                            }
                        assert url == TOKEN and form
                        return tokens(nonce["value"])

                    def helper_browser(url):
                        query = parse_qs(urlsplit(url).query)
                        nonce["value"] = query["nonce"][0]
                        callback = query["redirect_uri"][0]

                        def finish_callback():
                            response = httpx.get(
                                callback
                                + "?"
                                + urlencode(
                                    {
                                        "state": query["state"][0],
                                        "code": "synthetic-code",
                                        "client_id": client_id,
                                    }
                                ),
                                trust_env=False,
                            )
                            assert response.status_code == 200

                        helper_thread = threading.Thread(target=finish_callback)
                        helper_thread.start()
                        callback_threads.append(helper_thread)
                        return True

                    # The HTTPS helper origin is an explicit routing double to this
                    # disposable loopback backend, not a disabled certificate check.
                    connect(
                        "https://mealf-helper.invalid",
                        pair_code,
                        request=helper_request,
                        open_browser=helper_browser,
                        host=lambda: "urn:uuid:" + str(uuid4()),
                    )
                    for helper_thread in callback_threads:
                        helper_thread.join(timeout=5)
                        assert not helper_thread.is_alive()
                    expect(
                        panel.get_by_text("Connected to your ChatGPT plan", exact=True)
                    ).to_be_visible(timeout=10000)
                    panel.get_by_role(
                        "button", name="Choose an available model", exact=True
                    ).click()
                    panel.get_by_label("ChatGPT model", exact=True).select_option("synthetic-text")
                    panel.get_by_role("button", name="Save", exact=True).click()
                    expect(
                        panel.get_by_text("ChatGPT model: synthetic-text", exact=True)
                    ).to_be_visible()
                    panel.screenshot(path=str(captures / "connected-desktop.png"))

                    def audit():
                        page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                        findings = page.evaluate(
                            "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))"
                        )
                        assert findings == [], findings
                        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")

                    audit()
                    page.get_by_role("navigation").get_by_role(
                        "button", name="Recipes", exact=True
                    ).click()
                    page.get_by_role("button", name="Import recipe", exact=True).first.click()
                    page.get_by_label("AI account for this import", exact=True).select_option(
                        "chatgpt"
                    )
                    page.get_by_label("Recipe text", exact=True).fill(
                        "Synthetic recipe text: cook 200 g pasta for two portions."
                    )
                    page.get_by_label("Send this recipe text to my ChatGPT", exact=False).check()
                    audit()
                    page.get_by_role("button", name="Prepare preview", exact=True).click()
                    page.get_by_role("button", name="Review", exact=True).last.click(timeout=15000)
                    expect(
                        page.get_by_role("heading", name="Review your import", exact=True)
                    ).to_be_visible()
                    rows = page.evaluate(
                        "async()=> (await(await fetch('/api/v1/recipes',{headers:{'X-Mealf-Client':'pwa'}})).json()).items"
                    )
                    assert rows == []
                    page.get_by_label("Recipe name", exact=True).fill("Reviewed personal import")
                    page.get_by_role("button", name="Save", exact=True).last.click()
                    expect(
                        page.get_by_role("heading", name="Reviewed personal import", exact=True)
                    ).to_be_visible(timeout=10000)

                    page.get_by_role("navigation").get_by_role(
                        "button", name="Settings", exact=True
                    ).click()
                    settings_section(page, "Your household")
                    page.get_by_label("Language", exact=True).select_option("de")
                    settings_section(page, "Design-Bibliothek")
                    page.get_by_role("radio", name="After Dark", exact=False).check()
                    page.set_viewport_size({"width": 390, "height": 844})
                    settings_section(page, "Dein ChatGPT-Abo")
                    panel = page.locator(".chatgpt-settings")
                    expect(
                        panel.get_by_text("Mit deinem ChatGPT-Abo verbunden", exact=True)
                    ).to_be_visible()
                    expect(page.locator(".toast")).to_have_count(0, timeout=5000)
                    audit()
                    panel.screenshot(path=str(captures / "connected-phone-de-dark.png"))
                    page.get_by_role("navigation").get_by_role(
                        "button", name="Rezepte", exact=True
                    ).click()
                    page.get_by_role("button", name="Rezept importieren", exact=True).first.click()
                    page.get_by_label("KI-Konto für diesen Import", exact=True).select_option(
                        "chatgpt"
                    )
                    page.get_by_label("Rezepttext", exact=True).fill(
                        "Offline personal recipe text: simmer rice for two servings."
                    )
                    page.get_by_label(
                        "Sende diesen Rezepttext an mein ChatGPT", exact=False
                    ).check()
                    audit()
                    page.screenshot(path=str(captures / "import-phone-de-dark.png"), full_page=True)
                    context.set_offline(True)
                    page.get_by_role("button", name="Vorschau vorbereiten", exact=True).click()
                    page.wait_for_function(
                        "async()=> { const names=await indexedDB.databases(); const name=names.find(v=>v.name?.startsWith('mealf:'))?.name; if(!name)return false; const db=await new Promise((resolve,reject)=>{const r=indexedDB.open(name);r.onsuccess=()=>resolve(r.result);r.onerror=reject;}); const rows=await new Promise((resolve,reject)=>{const r=db.transaction('imports').objectStore('imports').getAll();r.onsuccess=()=>resolve(r.result);r.onerror=reject;});db.close();return rows.some(v=>v.state==='queued'&&v.body.ai_account==='chatgpt');}"
                    )
                    page.reload()
                    expect(
                        page.get_by_role("heading", name="Deine Küche", exact=True)
                    ).to_be_visible(timeout=10000)
                    context.set_offline(False)
                    page.get_by_role("navigation").get_by_role(
                        "button", name="Rezepte", exact=True
                    ).click()
                    page.get_by_role("button", name="Rezept importieren", exact=True).first.click()
                    try:
                        page.get_by_role("button", name="Prüfen", exact=True).last.click(
                            timeout=15000
                        )
                    except Exception:
                        with app.state.database.connect() as db:
                            print(
                                "Synthetic server import diagnostics:",
                                [
                                    dict(row)
                                    for row in db.execute(
                                        "SELECT state,error_code FROM import_draft"
                                    ).fetchall()
                                ],
                            )
                        print(
                            "Synthetic device import diagnostics:",
                            page.evaluate(
                                "async()=>{const names=await indexedDB.databases();const name=names.find(v=>v.name?.startsWith('mealf:'))?.name;if(!name)return [];const db=await new Promise(resolve=>{const r=indexedDB.open(name);r.onsuccess=()=>resolve(r.result);});const rows=await new Promise(resolve=>{const r=db.transaction('imports').objectStore('imports').getAll();r.onsuccess=()=>resolve(r.result);});db.close();return rows.map(v=>({state:v.state,error:v.error}));}"
                            ),
                        )
                        raise
                    expect(
                        page.get_by_role("heading", name="Import prüfen", exact=True)
                    ).to_be_visible()
                    assert (
                        len(
                            [
                                request
                                for request in calls
                                if request.url.path.endswith("/responses")
                            ]
                        )
                        == 2
                    )
                    assert not errors, errors
                    context.close()
                    browser.close()
                    print(
                        "PASS: real PWA pairing/standalone loopback helper, signed-token verification, personal model selection, EN desktop/DE dark phone/Axe, explicit reviewed save and offline queue/reload. OpenAI identity/inference and HTTPS helper-origin routing are synthetic; no live subscription or Windows/iPhone execution claimed."
                    )
        finally:
            server.should_exit = True
            thread.join(timeout=15)
            if thread.is_alive():
                raise RuntimeError("Synthetic backend did not stop")


if __name__ == "__main__":
    main()
