import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "browser_test_errors", Path(__file__).parents[1] / "scripts/browser_test_errors.py"
)
assert spec and spec.loader
browser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(browser)
BASE = "https://127.0.0.1:5152"
URL = BASE + "/api/v1/sync/state?cursor=0"
ERROR = {
    "name": "Fetch API cannot load https",
    "message": "/127.0.0.1:5152/api/v1/sync/state?cursor=0 due to access control checks.",
    "stack": f"Fetch API cannot load {URL} due to access control checks.\n    at perform ({BASE}/app/assets/client.js:9:1)",
    "outage": True,
}
FAILED = [{"url": URL, "outage": True}]


@pytest.mark.parametrize(
    "query,expected",
    [
        ("&_mealf_sync=21ef346e-23a1-48c7-9a24-218e692f40aa", True),
        ("&_mealf_sync=invalid", False),
        ("&_mealf_sync=21ef346e-23a1-48c7-9a24-218e692f40aa&extra=1", False),
        ("&other=21ef346e-23a1-48c7-9a24-218e692f40aa", False),
    ],
)
def test_only_the_actual_sync_nonce_shape_extends_the_controlled_outage(query, expected):
    error = {
        **ERROR,
        "message": ERROR["message"].replace("?cursor=0", "?cursor=0" + query),
        "stack": ERROR["stack"].replace("?cursor=0", "?cursor=0" + query),
    }
    failed = [{"url": URL + query, "outage": True}]
    assert browser.expected_webkit_outage("webkit", BASE, error, failed) is expected
    assert not browser.expected_webkit_outage("webkit", BASE, error, [])
    assert browser.unexpected_browser_errors("webkit", BASE, [error], failed, [{"kind": "error"}])[
        0
    ] == {"kind": "error"}


def test_native_diagnostic_requires_a_real_matching_outage_request():
    assert browser.unexpected_browser_errors("webkit", BASE, [ERROR], FAILED, []) == []
    assert browser.unexpected_browser_errors("webkit", BASE, [ERROR], [], []) == [ERROR]
    assert browser.unexpected_browser_errors(
        "webkit", BASE, [ERROR], [{"url": URL, "outage": False}], []
    ) == [ERROR]


@pytest.mark.parametrize(
    "change",
    [
        {"outage": False},
        {"name": "TypeError"},
        {"name": "Error"},
        {"message": ERROR["message"].replace("127.0.0.1", "example.com")},
        {"message": ERROR["message"].replace("5152", "8080")},
        {"message": ERROR["message"].replace("sync/state", "recipes")},
        {"message": ERROR["message"].replace("cursor=0", "cursor=invalid")},
        {"message": ERROR["message"] + " extra"},
        {"stack": "TypeError: actual bug\n    at perform (client.js:9:1)"},
    ],
)
def test_unknown_or_outside_fixture_errors_remain_fatal(change):
    error = {**ERROR, **change}
    assert browser.unexpected_browser_errors("webkit", BASE, [error], FAILED, []) == [error]


@pytest.mark.parametrize("engine", ["chromium", "firefox"])
def test_other_engines_never_reclassify_page_errors(engine):
    assert browser.unexpected_browser_errors(engine, BASE, [ERROR], FAILED, []) == [ERROR]


def test_window_exceptions_and_unhandled_rejections_always_remain_fatal():
    failures = [
        {"kind": "error", **ERROR},
        {"kind": "unhandledrejection", **ERROR},
    ]
    assert browser.unexpected_browser_errors("webkit", BASE, [ERROR], FAILED, failures) == failures
