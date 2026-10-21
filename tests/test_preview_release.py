import importlib.util
from pathlib import Path
from urllib.error import HTTPError

import pytest

spec = importlib.util.spec_from_file_location(
    "preview_release", Path(__file__).parents[1] / "scripts/preview_release.py"
)
assert spec and spec.loader
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
TAG = "poc-20261021.5"
IMAGE = "ghcr.io/cloudcookch/mealf-server"
DIGEST = "sha256:" + "a" * 64


def published():
    return {
        "tag_name": TAG,
        "draft": False,
        "prerelease": True,
        "body": f"Image: `{IMAGE}@{DIGEST}`\n\nNotes",
    }


def test_completed_preview_retry_preserves_published_digest():
    assert release.completed_digest(published(), TAG, IMAGE) == DIGEST
    assert release.completed_digest(None, TAG, IMAGE) is None


@pytest.mark.parametrize(
    "change",
    [
        {"tag_name": "poc-20261021.4"},
        {"draft": True},
        {"prerelease": False},
        {"body": "Missing image proof"},
        {"body": f"Image: `{IMAGE}:preview`"},
        {"body": f"Image: `ghcr.io/someone/else@{DIGEST}`"},
    ],
)
def test_incomplete_or_mismatched_release_is_never_overwritten(change):
    with pytest.raises(ValueError):
        release.completed_digest({**published(), **change}, TAG, IMAGE)


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500])
def test_only_not_found_allows_a_new_preview(monkeypatch, status):
    def fail(*args, **kwargs):
        raise HTTPError("https://api.github.com/example", status, "synthetic", {}, None)

    monkeypatch.setattr(release, "urlopen", fail)
    if status == 404:
        assert release.fetch_release("owner/repo", TAG, "synthetic") is None
    else:
        with pytest.raises(HTTPError):
            release.fetch_release("owner/repo", TAG, "synthetic")
