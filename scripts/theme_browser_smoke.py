"""Theme preferences in real engines; synthetic disposable profiles and backend only.

Checks actual controls, offline persistence, cross-tab admin reuse, early boot,
OS overrides and contrast. Linux WebKit is not a physical iPhone installation.
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


def contrast(first, second):
    def luminance(value):
        if len(value) == 4:
            value = "#" + "".join(c * 2 for c in value[1:])
        rgb = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    a, b = sorted([luminance(first), luminance(second)])
    return (b + 0.05) / (a + 0.05)


def main():
    engine = os.environ.get("AIRCOOKER_LAYOUT_ENGINE", "chromium")
    outage = engine == "webkit" or os.environ.get("MEALF_THEME_NETWORK_OUTAGE") == "1"
    captures = Path(os.environ.get("AIRCOOKER_SCREENSHOT_DIR", "build/theme-browser")) / engine
    captures.mkdir(parents=True, exist_ok=True)
    evidence = []
    with TemporaryDirectory(prefix="mealf-themes-") as temporary:
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
                raise RuntimeError("Theme test server not ready")
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
                    str(Path(temporary) / "profile"),
                    viewport={"width": 390, "height": 844},
                    color_scheme="light",
                    **options,
                )
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                axe = Path("frontend/node_modules/axe-core/axe.min.js").read_text()

                def choose(name):
                    radio = page.get_by_role("radio", name=name, exact=True)
                    radio.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})")
                    radio.check()

                def check(theme, mode, screen=page):
                    expect(screen.locator("html")).to_have_attribute("data-theme", theme)
                    tokens = screen.evaluate(
                        """() => {
                        const s=getComputedStyle(document.documentElement);
                        return Object.fromEntries(['canvas','surface','ink','muted','soft','hover',
                          'accent','accent-hover','on-accent','accent-soft','accent-ink','accent-muted',
                          'focus','selection','control-border','danger','danger-soft','danger-ink',
                          'warning-soft','warning-ink'].map(k=>[k,s.getPropertyValue('--'+k).trim()]));
                        }"""
                    )
                    # Media-query change events are asynchronous in WebKit. Require
                    # metadata to settle to the actual palette, rather than sample
                    # it before the browser dispatches that native event.
                    expect(screen.locator('meta[name="theme-color"]').first).to_have_attribute(
                        "content", tokens["canvas"]
                    )
                    expect(screen.locator('meta[name="color-scheme"]')).to_have_attribute(
                        "content", mode
                    )
                    assert screen.locator("html").evaluate(
                        "e=>getComputedStyle(e).colorScheme"
                    ) == ("light dark" if theme == "flo" else mode)
                    pairs = [
                        ("ink", "canvas", 4.5),
                        ("ink", "surface", 4.5),
                        ("ink", "soft", 4.5),
                        ("muted", "canvas", 4.5),
                        ("muted", "surface", 4.5),
                        ("muted", "soft", 4.5),
                        ("accent", "canvas", 4.5),
                        ("accent", "surface", 4.5),
                        ("on-accent", "accent", 4.5),
                        ("on-accent", "accent-hover", 4.5),
                        ("accent-ink", "accent-soft", 4.5),
                        ("accent-muted", "accent-soft", 4.5),
                        ("danger", "surface", 4.5),
                        ("danger-ink", "danger-soft", 4.5),
                        ("warning-ink", "warning-soft", 4.5),
                        ("ink", "selection", 4.5),
                        ("control-border", "surface", 3),
                        ("focus", "surface", 3),
                    ]
                    ratios = {
                        a + "/" + b: round(contrast(tokens[a], tokens[b]), 3)
                        for a, b, minimum in pairs
                    }
                    for a, b, minimum in pairs:
                        assert contrast(tokens[a], tokens[b]) >= minimum, (
                            theme,
                            mode,
                            a,
                            b,
                            ratios,
                        )
                    screen.evaluate(axe)
                    violations = screen.evaluate(
                        """async()=> (await axe.run(document,{runOnly:{type:'tag',values:
                        ['wcag2a','wcag2aa','wcag21aa']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))"""
                    )
                    assert violations == [], (theme, mode, violations)
                    assert screen.evaluate("document.documentElement.scrollWidth<=innerWidth"), (
                        theme,
                        mode,
                        "page overflow",
                    )
                    evidence.append({"theme": theme, "mode": mode, "ratios": ratios})

                page.goto(base + "/app/")
                check("flo", "light")
                page.get_by_role("button", name="Explore the demo").click()
                page.get_by_role("navigation").get_by_role("button", name="Settings").click()
                expect(page.get_by_role("group", name="Theme library")).to_be_visible()
                expect(page.get_by_role("radio", name="Flo", exact=True)).to_be_checked()
                for theme, label, mode in [
                    ("after-dark", "After Dark", "dark"),
                    ("sunday", "Sunday", "light"),
                    ("flo", "Flo", "light"),
                ]:
                    choose(label)
                    check(theme, mode)
                    if theme != "flo":
                        if theme == "sunday":
                            page.set_viewport_size({"width": 1440, "height": 1000})
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Home", exact=True
                        ).click()
                        expect(page.locator(".featured-meal img")).to_be_visible()
                        page.locator(".featured-meal img").evaluate(
                            "async image=>{await image.decode();}"
                        )
                        page.screenshot(path=str(captures / (theme + "-home.png")))
                        page.get_by_role("navigation").get_by_role(
                            "button", name="Settings"
                        ).click()
                        page.set_viewport_size({"width": 390, "height": 844})
                    # Explicit palettes hold under the opposite system setting.
                    page.emulate_media(color_scheme="dark")
                    check(theme, "dark" if theme == "flo" else mode)
                    page.emulate_media(color_scheme="light")
                # Native radio arrow navigation changes the applied theme.
                page.get_by_role("radio", name="Flo", exact=True).focus()
                page.keyboard.press("ArrowRight")
                expect(page.get_by_role("radio", name="After Dark", exact=True)).to_be_checked()
                check("after-dark", "dark")
                page.get_by_role(
                    "radio", name="After Dark", exact=True
                ).scroll_into_view_if_needed()
                page.screenshot(path=str(captures / "after-dark-settings-phone.png"))
                page.wait_for_function("!!navigator.serviceWorker.controller")
                if outage:
                    # This WebKit build reports an internal engine error on
                    # automation-offline reload. Exercise real connection
                    # refusal instead; never mock or replace the worker cache.
                    server.should_exit = True
                    thread.join(timeout=10)
                    assert not thread.is_alive(), "Backend outage was not established"
                else:
                    context.set_offline(True)
                page.reload()
                expect(page.get_by_role("heading", name="Your kitchen")).to_be_visible()
                page.get_by_role("navigation").get_by_role("button", name="Settings").click()
                expect(page.get_by_role("radio", name="After Dark", exact=True)).to_be_checked()
                choose("Sunday")
                page.reload()
                expect(page.locator("html")).to_have_attribute("data-theme", "sunday")
                page.get_by_role("navigation").get_by_role("button", name="Settings").click()
                page.get_by_label("Language", exact=True).select_option("de")
                expect(page.get_by_role("group", name="Design-Bibliothek")).to_be_visible()
                check("sunday", "light")
                page.get_by_role("radio", name="Sunday", exact=True).scroll_into_view_if_needed()
                page.screenshot(path=str(captures / "sunday-settings-phone-de.png"))
                if outage:
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
                    for _ in range(100):
                        if server.started:
                            break
                        time.sleep(0.05)
                    else:
                        raise RuntimeError("Backend did not recover after outage")
                else:
                    context.set_offline(False)
                admin = context.new_page()
                admin.goto(base)
                check("sunday", "light", admin)
                admin.get_by_label("Theme", exact=True).select_option("after-dark")
                expect(page.locator("html")).to_have_attribute("data-theme", "after-dark")
                expect(page.get_by_role("radio", name="After Dark", exact=True)).to_be_checked()
                check("after-dark", "dark", admin)
                admin.reload()
                expect(admin.get_by_label("Theme", exact=True)).to_have_value("after-dark")
                admin.set_viewport_size({"width": 1440, "height": 1000})
                admin.screenshot(path=str(captures / "after-dark-admin-desktop.png"))
                # The exact controller works before the React bundle starts.
                page.evaluate(
                    "async()=>{for(const r of await navigator.serviceWorker.getRegistrations())await r.unregister();}"
                )
                early = context.new_page()
                early.route("**/assets/*.js", lambda route: route.abort())
                early.goto(base + "/app/")
                expect(early.locator("html")).to_have_attribute("data-theme", "after-dark")
                assert early.locator("#root").inner_html() == ""
                early.add_init_script("""(() => {
                  const get=Storage.prototype.getItem;
                  Storage.prototype.getItem=function(key){
                    if(key==='mealf.appearance.v1')throw new DOMException('Test denial','SecurityError');
                    return get.call(this,key);
                  };
                })();""")
                early.reload()
                expect(early.locator("html")).to_have_attribute("data-theme", "flo")
                early.close()
                page.get_by_role("navigation").get_by_role(
                    "button", name="Start", exact=True
                ).click()
                page.get_by_role("navigation").get_by_role("button", name="Einstellungen").click()
                page.set_viewport_size({"width": 320, "height": 568})
                check("after-dark", "dark")
                # A rejected preference write changes appearance but does not imply persistence.
                page.evaluate(
                    """() => {
                    window.savedSetItem=Storage.prototype.setItem;
                    Storage.prototype.setItem=function(key,value){
                      if(key==='mealf.appearance.v1')throw new DOMException('Test quota','QuotaExceededError');
                      return window.savedSetItem.call(this,key,value);
                    }; }"""
                )
                choose("Sunday")
                expect(page.locator(".theme-status")).to_contain_text("Browserspeicher")
                expect(page.locator("html")).to_have_attribute("data-theme", "sunday")
                page.evaluate("() => { Storage.prototype.setItem=window.savedSetItem; }")
                # Invalid stored values safely fall back; no arbitrary CSS/HTML injection.
                page.evaluate("localStorage.setItem('mealf.appearance.v1','not-a-theme')")
                page.reload()
                expect(page.locator("html")).to_have_attribute("data-theme", "flo")
                admin.get_by_label("Theme", exact=True).select_option("sunday")
                page.get_by_role("navigation").get_by_role("button", name="Einstellungen").click()
                page.get_by_label("Sprache", exact=True).select_option("en")
                page.set_viewport_size({"width": 1440, "height": 1000})
                page.get_by_role("radio", name="Sunday", exact=True).scroll_into_view_if_needed()
                page.screenshot(path=str(captures / "sunday-settings-desktop.png"))
                page.get_by_role("navigation").get_by_role(
                    "button", name="Home", exact=True
                ).click()
                assert errors == [], errors
                context.close()
            (captures / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
            print(
                f"PASS: {engine} theme switching, native radio keys, offline reload, admin sharing, early boot, storage failure and contrast/Axe"
            )
        finally:
            server.should_exit = True
            thread.join(timeout=10)


if __name__ == "__main__":
    main()
