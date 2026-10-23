"""Real account management, PWA login and role restrictions with synthetic household data."""

import os
import shutil
import socket
import threading
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import httpx
import uvicorn
from playwright.sync_api import expect, sync_playwright

from mealf.app import create_app


def main():
    with TemporaryDirectory(prefix="mealf-users-") as directory:
        root = Path(directory)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        os.environ["BASE_URL"] = base
        os.environ["LOG_SETUP_TOKEN"] = "false"
        app = create_app(root, run_worker=False)
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
            with httpx.Client(base_url=base, trust_env=False) as operator:
                setup = operator.post(
                    "/api/v1/setup",
                    headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
                    json={
                        "name": "Synthetic shared kitchen",
                        "username": "cook",
                        "password": "synthetic admin password",
                        "device_id": str(uuid4()),
                    },
                )
                setup.raise_for_status()
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=shutil.which("chromium") or shutil.which("google-chrome"),
                    args=["--no-sandbox"],
                )
                admin_context = browser.new_context(viewport={"width": 1280, "height": 900})
                page = admin_context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base + "/admin/")
                page.locator('#login input[name="username"]').fill("cook")
                page.locator('#login input[name="password"]').fill("synthetic admin password")
                page.locator('#login button[type="submit"]').click()
                expect(page.locator("#dashboard")).to_be_visible()
                page.locator('[data-page-link="security"]').click()
                create = page.locator("#user-create")
                create.get_by_label("Username", exact=True).fill("member")
                create.get_by_label("New password (at least 12 characters)", exact=True).fill(
                    "synthetic member password"
                )
                create.get_by_role("button", name="Add user", exact=True).click()
                member = page.locator("#users form").filter(
                    has=page.locator("legend", has_text="member")
                )
                expect(member).to_be_visible()
                expect(member.get_by_role("combobox", name="Role", exact=True)).to_have_value(
                    "user"
                )
                # No account secrets or hashes appear in API projections or rendered markup.
                users = page.evaluate("()=>request('/api/v1/admin/users')")
                assert all(set(user) == {"id", "username", "role", "active"} for user in users)
                member_id = next(user["id"] for user in users if user["username"] == "member")
                user_context = browser.new_context(viewport={"width": 390, "height": 844})
                user_page = user_context.new_page()
                user_page.on("pageerror", lambda error: errors.append(str(error)))

                def sign_in(password):
                    user_page.goto(base + "/app/")
                    user_page.get_by_role("button", name="Open your kitchen", exact=True).click()
                    user_page.get_by_label("Username", exact=True).fill("member")
                    user_page.get_by_label("Password", exact=True).fill(password)
                    user_page.get_by_role("button", name="Sign in", exact=True).click()
                    expect(
                        user_page.get_by_role("heading", name="Your kitchen", exact=True)
                    ).to_be_visible()

                def status(path, method="GET", body=None):
                    return user_page.evaluate(
                        "async args => {const response=await fetch(args.path,{method:args.method,headers:{'X-Mealf-Client':'pwa','Content-Type':'application/json','X-CSRF-Token':decodeURIComponent(document.cookie.split('; ').find(row=>row.startsWith('mealf_pwa_csrf='))?.split('=')[1]??'')},body:args.body===null?undefined:JSON.stringify(args.body)});return response.status}",
                        {"path": path, "method": method, "body": body},
                    )

                sign_in("synthetic member password")
                assert status("/api/v1/auth/me") == 200
                assert status("/api/v1/ai/status") == 200
                assert status("/api/v1/admin/users") == 403
                assert status("/api/v1/admin/users/" + member_id, "PATCH", {"role": "admin"}) == 403
                user_page.get_by_role("button", name="Settings", exact=True).click()
                user_page.get_by_text("Your household", exact=True).click()
                expect(user_page.locator('a[href^="/admin/"]')).to_have_count(0)
                expect(user_page.get_by_text("AI recipe import", exact=True)).to_have_count(0)
                # The admin console cannot establish a cookie session for regular users.
                console = user_context.new_page()
                console.goto(base + "/admin/")
                console.locator('#login input[name="username"]').fill("member")
                console.locator('#login input[name="password"]').fill("synthetic member password")
                console.locator('#login button[type="submit"]').click()
                expect(console.locator("#status")).to_contain_text("admin_required")
                expect(console.locator("#dashboard")).to_be_hidden()
                console.close()
                member.get_by_role("combobox", name="Role", exact=True).select_option("admin")
                member.get_by_role("button", name="Save changes", exact=True).click()
                expect(page.locator("#status")).to_have_text("Changes saved.")
                assert status("/api/v1/auth/me") == 401
                # Return to the sign-in screen after a real reload, then check the new role.
                sign_in("synthetic member password")
                assert status("/api/v1/admin/users") == 200
                member = page.locator("#users form").filter(
                    has=page.locator("legend", has_text="member")
                )
                member.get_by_role("combobox", name="Role", exact=True).select_option("user")
                member.get_by_label("New password (leave blank to keep)", exact=True).fill(
                    "replacement member password"
                )
                member.get_by_role("button", name="Save changes", exact=True).click()
                expect(page.locator("#status")).to_have_text("Changes saved.")
                assert status("/api/v1/auth/me") == 401
                sign_in("replacement member password")
                assert status("/api/v1/admin/users") == 403
                member = page.locator("#users form").filter(
                    has=page.locator("legend", has_text="member")
                )
                member.get_by_label("Account enabled", exact=True).uncheck()
                member.get_by_role("button", name="Save changes", exact=True).click()
                expect(page.locator("#status")).to_have_text("Changes saved.")
                assert status("/api/v1/auth/me") == 401
                own = page.locator("#users form").filter(
                    has=page.locator("legend", has_text="cook")
                )
                own.get_by_role("combobox", name="Role", exact=True).select_option("user")
                own.get_by_role("button", name="Save changes", exact=True).click()
                expect(page.locator("#status")).to_contain_text("last_admin_required")
                # Check actual narrow layout, keyboard labels and contrast on the new UI.
                page.set_viewport_size({"width": 390, "height": 844})
                page.evaluate(Path("frontend/node_modules/axe-core/axe.min.js").read_text())
                violations = page.evaluate(
                    "async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})).violations"
                )
                assert not violations, [
                    (item["id"], item["nodes"][0]["html"]) for item in violations
                ]
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                assert not errors, errors
                browser.close()
        finally:
            server.should_exit = True
            thread.join(timeout=10)
    print(
        "PASS: real user management, regular/admin PWA access, role/password/disable revocation, last-admin protection, mobile Axe"
    )


if __name__ == "__main__":
    main()
