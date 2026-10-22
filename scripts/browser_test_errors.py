"""Keep genuine browser errors fatal during a controlled WebKit outage test."""

import re
from urllib.parse import urlsplit


def expected_webkit_outage(engine, base, error, failed_requests):
    # Playwright maps WebKit's source=javascript console messages to pageerror,
    # splitting at the first colon (the URL scheme). This native message is also
    # emitted for caught fetch failures, without a window error/rejection event.
    if (
        engine != "webkit"
        or urlsplit(base).scheme != "https"
        or urlsplit(base).hostname != "127.0.0.1"
        or not error.get("outage")
        or error.get("name") != "Fetch API cannot load https"
    ):
        return False
    suffix = " due to access control checks."
    message = error.get("message", "")
    if not re.fullmatch(
        re.escape(base.removeprefix("https:/"))
        + r"/api/v1/sync/state\?cursor=\d+"
        + r"(?:&_mealf_sync=[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})?"
        + re.escape(suffix),
        message,
    ):
        return False
    failed_url = "https:/" + message.removesuffix(suffix)
    stack = error.get("stack", "")
    if stack and not stack.startswith(f"Fetch API cannot load {failed_url}{suffix}\n"):
        return False
    return any(r.get("outage") and r.get("url") == failed_url for r in failed_requests)


def unexpected_browser_errors(engine, base, page_errors, failed_requests, window_errors):
    # Actual window error/unhandledrejection events are NEVER reclassified, even
    # if their text happens to match the native diagnostic. All other pageerrors
    # remain fatal, including outside-outage, foreign-origin and unrelated routes.
    return list(window_errors) + [
        error
        for error in page_errors
        if not expected_webkit_outage(engine, base, error, failed_requests)
    ]
