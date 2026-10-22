"""Real PWA/API/offline/worker flow with explicit subscription and vendor transport doubles.

No push vendor is contacted. CDP injects a push event into the real service worker;
this does not establish Safari, OS display, user permission-dialog or live delivery support.
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
from browser_settings import settings_section
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from playwright.sync_api import expect, sync_playwright

from mealf.app import create_app
from mealf.jobs import claim, finish
from mealf.webpush import PushResponse, encoded


def main():
    with TemporaryDirectory(prefix="mealf-push-browser-") as temporary:
        root = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        app = create_app(root, run_worker=False)
        # Explicit test-only public-URL/transport substitution, never a production bypass.
        app.state.reminders.available = True
        delivered = []
        app.state.reminders.transport.send = lambda *args: delivered.append(args) or PushResponse(
            201
        )
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
            raise RuntimeError("Browser fixture server did not start")
        receiver = (
            ec.generate_private_key(ec.SECP256R1())
            .public_key()
            .public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        )
        fixture = {
            "endpoint": "https://web.push.apple.com/synthetic-browser-subscription",
            "keys": {"p256dh": encoded(receiver), "auth": encoded(b"synthetic-auth!!")},
        }
        subscription_double = """fixture => {
          window.TEST_ONLY_pushReads=0;
          // Headless Chrome pre-denies prompts. Model an initial default permission
          // explicitly; subsequent permission behavior comes from the real context.
          const permission=Object.getOwnPropertyDescriptor(Notification,'permission');
          Object.defineProperty(Notification,'permission',{configurable:true,get:()=>
            localStorage.getItem('TEST-ONLY:permission-ready') ? permission.get.call(Notification) : 'default'});
          const storageKey='TEST-ONLY:push-subscription';
          const wrap=value=>value && ({endpoint:value.endpoint,
            options:{applicationServerKey:Uint8Array.from(value.key).buffer},
            toJSON:()=>({endpoint:value.endpoint,keys:fixture.keys}),
            unsubscribe:async()=>{localStorage.removeItem(storageKey);return true;}});
          const manager={
            getSubscription:async()=>{
              window.TEST_ONLY_pushReads++;
              return wrap(JSON.parse(localStorage.getItem(storageKey)||'null'));
            },
            subscribe:async options=>{
              if(!options.userVisibleOnly || !options.applicationServerKey) throw Error('unsafe_options');
              const value={...fixture,key:[...new Uint8Array(options.applicationServerKey)]};
              localStorage.setItem(storageKey,JSON.stringify(value));return wrap(value);
            }
          };
          Object.defineProperty(ServiceWorkerRegistration.prototype,'pushManager',{get:()=>manager});
        }"""
        captures = Path(os.environ.get("MEALF_SCREENSHOT_DIR", "build/push-browser"))
        captures.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=os.environ.get("CHROMIUM_EXECUTABLE")
                    or shutil.which("chromium")
                    or shutil.which("google-chrome"),
                    args=["--no-sandbox"],
                )
                context = browser.new_context(viewport={"width": 1440, "height": 1000})
                context.add_init_script(
                    "(" + subscription_double + ")(" + json.dumps(fixture) + ")"
                )
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                cdp = context.new_cdp_session(page)
                registrations = []
                cdp.on(
                    "ServiceWorker.workerRegistrationUpdated",
                    lambda data: registrations.extend(data["registrations"]),
                )
                cdp.send("ServiceWorker.enable")
                page.goto(base + "/app/")
                page.get_by_role("button", name="Open your kitchen", exact=True).click()
                page.get_by_label("Username", exact=True).fill("cook")
                page.get_by_label("Password", exact=True).fill(
                    "synthetic reminder kitchen password"
                )
                page.get_by_label("One-time setup token", exact=True).fill(
                    (root / "config/setup-token").read_text()
                )
                page.get_by_label("Kitchen name", exact=True).fill("Browser kitchen")
                page.get_by_label("Household time zone", exact=True).fill("Europe/Zurich")
                page.get_by_role("button", name="Set up your kitchen", exact=True).click()
                expect(page.get_by_role("heading", name="Your kitchen")).to_be_visible(
                    timeout=15000
                )
                page.wait_for_function("!!navigator.serviceWorker.controller")
                page.get_by_role("navigation").get_by_role(
                    "button", name="Settings", exact=True
                ).click()
                settings_section(page, "Meal reminders")
                expect(
                    page.get_by_role("button", name="Connect notifications", exact=True)
                ).to_be_enabled()
                assert page.evaluate("window.TEST_ONLY_pushReads") == 0
                context.grant_permissions(["notifications"])
                page.evaluate("localStorage.setItem('TEST-ONLY:permission-ready','1')")
                page.get_by_role("button", name="Connect notifications", exact=True).click()
                enabled = page.get_by_label("Enable meal reminders", exact=True)
                expect(enabled).to_be_visible()
                assert page.evaluate("window.TEST_ONLY_pushReads") > 0
                enabled.check()
                page.locator('input[type="time"]').nth(2).fill("18:45")
                page.get_by_role("button", name="Save reminder settings", exact=True).click()
                expect(page.get_by_text("Reminder settings saved.", exact=True)).to_be_visible()
                status = page.evaluate(
                    "async()=> (await fetch('/api/v1/notifications/push',{headers:{'X-Mealf-Client':'pwa'}})).json()"
                )
                assert status["subscribed"] and status["preferences"]["dinner"] == "18:45"
                group = page.locator(".settings-group").filter(
                    has=page.get_by_role("heading", name="Meal reminders", exact=True)
                )
                axe = Path("frontend/node_modules/axe-core/axe.min.js").read_text()

                def audit():
                    page.evaluate(axe)
                    violations = page.evaluate(
                        "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))"
                    )
                    assert violations == [], violations

                audit()
                page.screenshot(
                    path=str(captures / "mealf-reminders-desktop.png"),
                    full_page=True,
                    animations="disabled",
                )
                group.screenshot(
                    path=str(captures / "mealf-reminders-controls-desktop.png"),
                    animations="disabled",
                )
                context.set_offline(True)
                page.locator('input[type="time"]').nth(2).fill("19:10")
                expect(
                    page.get_by_role("button", name="Save reminder settings", exact=True)
                ).to_be_disabled()
                page.reload()
                page.get_by_role("navigation").get_by_role(
                    "button", name="Settings", exact=True
                ).click()
                settings_section(page, "Meal reminders")
                expect(page.locator('input[type="time"]').nth(2)).to_have_value("19:10")
                # navigator.onLine is only a hint (Chromium may report true after a SW reload).
                # A failed save must still retain the draft and leave server settings unchanged.
                save_button = page.get_by_role("button", name="Save reminder settings", exact=True)
                if save_button.is_enabled():
                    save_button.click()
                    expect(
                        page.get_by_text("Could not update reminders.", exact=False)
                    ).to_be_visible()
                with app.state.database.connect() as db:
                    saved = json.loads(
                        db.execute("SELECT preferences FROM push_subscription").fetchone()[0]
                    )
                    assert saved["dinner"] == "18:45"
                context.set_offline(False)
                page.get_by_role("button", name="Save reminder settings", exact=True).click()
                expect(page.get_by_text("Reminder settings saved.", exact=True)).to_be_visible()
                with app.state.database.transaction() as db:
                    db.execute("UPDATE background_job SET state='done'")
                page.get_by_role("button", name="Send a test reminder", exact=True).click()
                expect(page.get_by_text("Delivery queued.", exact=True)).to_be_visible()
                job = claim(app.state.database)
                assert job and job["kind"] == "notification.test"
                app.state.reminders.deliver(job)
                assert finish(app.state.database, job) and len(delivered) == 1
                assert delivered[0][1]["body"] == "Your meal reminders are connected."
                page.reload()
                page.get_by_role("navigation").get_by_role(
                    "button", name="Settings", exact=True
                ).click()
                settings_section(page, "Meal reminders")
                expect(
                    page.get_by_text("Last accepted by delivery service:", exact=False)
                ).to_be_visible()
                settings_section(page, "Your household")
                page.get_by_label("Language", exact=True).select_option("de")
                page.set_viewport_size({"width": 390, "height": 844})
                page.emulate_media(color_scheme="dark")
                expect(
                    page.get_by_label("Mahlzeitenerinnerungen aktivieren", exact=True)
                ).to_be_checked()
                audit()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(
                    path=str(captures / "mealf-reminders-phone-de-dark.png"),
                    full_page=True,
                    animations="disabled",
                )
                group = page.locator(".settings-group").filter(
                    has=page.get_by_role("heading", name="Mahlzeitenerinnerungen", exact=True)
                )
                group.screenshot(
                    path=str(captures / "mealf-reminders-controls-phone-de-dark.png"),
                    animations="disabled",
                )
                settings_section(page, "Dein Haushalt")
                page.get_by_label("Sprache", exact=True).select_option("en")
                page.get_by_role("navigation").get_by_role(
                    "button", name="Home", exact=True
                ).click()
                page.get_by_role("button", name="New recipe", exact=True).click()
                page.get_by_label("Recipe name", exact=True).fill("Unsaved notification recipe")
                # Real worker-origin message, same path used by the notificationclick handler.
                worker = context.service_workers[0]
                worker.evaluate(
                    "async()=>{for(const client of await self.clients.matchAll({type:'window'}))client.postMessage({type:'MEAL_REMINDER',url:self.location.origin+'/app/?tab=calendar&day=2026-10-21'});}"
                )
                expect(
                    page.get_by_role("button", name="Open reminder", exact=True)
                ).to_be_disabled()
                expect(page.get_by_label("Recipe name", exact=True)).to_have_value(
                    "Unsaved notification recipe"
                )
                page.get_by_role("button", name="Save", exact=True).click()
                page.get_by_role("button", name="Open reminder", exact=True).click()
                expect(page.get_by_role("heading", name="Calendar", exact=True)).to_be_visible()
                # CDP injects standard payload into the actual push listener; no vendor contacted.
                registration = next(
                    item for item in registrations if item["scopeURL"] == base + "/app/"
                )
                cdp.send(
                    "ServiceWorker.deliverPushMessage",
                    {
                        "origin": base,
                        "registrationId": registration["registrationId"],
                        "data": json.dumps(
                            {
                                "body": "Synthetic receiver verification",
                                "url": "/app/?tab=settings",
                                "tag": "mealf-smoke",
                            }
                        ),
                    },
                )
                page.wait_for_function(
                    "async()=> (await (await navigator.serviceWorker.ready).getNotifications()).some(n=>n.tag==='mealf-smoke')"
                )
                awaitable = "async()=>{for(const n of await(await navigator.serviceWorker.ready).getNotifications())n.close();}"
                page.evaluate(awaitable)
                page.get_by_role("navigation").get_by_role(
                    "button", name="Settings", exact=True
                ).click()
                settings_section(page, "Meal reminders")
                page.get_by_role("button", name="Disconnect notifications", exact=True).click()
                expect(
                    page.get_by_role("button", name="Connect notifications", exact=True)
                ).to_be_visible()
                assert page.evaluate(
                    "async()=> !(await (await navigator.serviceWorker.ready).pushManager.getSubscription())"
                )
                cdp.send(
                    "Browser.setPermission",
                    {
                        "permission": {"name": "notifications"},
                        "setting": "denied",
                        "origin": base,
                        "browserContextId": cdp.send("Target.getTargetInfo")["targetInfo"][
                            "browserContextId"
                        ],
                    },
                )
                page.reload()
                page.get_by_role("navigation").get_by_role(
                    "button", name="Settings", exact=True
                ).click()
                settings_section(page, "Meal reminders")
                expect(page.get_by_text("Notifications are blocked.", exact=False)).to_be_visible()
                expect(
                    page.get_by_role("button", name="Connect notifications", exact=True)
                ).to_be_disabled()
                assert not errors, errors
                print(
                    json.dumps(
                        {
                            "result": "passed",
                            "api": "real",
                            "subscription_and_vendor": "explicit synthetic doubles",
                            "receiver": "real worker with CDP-injected push",
                            "offline_draft": True,
                            "editor_preserved": True,
                            "axe": "desktop EN/light and phone DE/dark",
                            "live_delivery": "not tested",
                        }
                    )
                )
                browser.close()
        finally:
            server.should_exit = True
            thread.join(timeout=10)


if __name__ == "__main__":
    main()
