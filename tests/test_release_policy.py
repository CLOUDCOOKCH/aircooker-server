"""Distribution boundaries: stable proof, version identity and immutable install assets."""

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def policy(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    # Resolve the same sibling modules as the real workflow invocation.
    for name in ("preview_gate", "preview_release"):
        monkeypatch.setitem(sys.modules, name, load(name))
    return load("release_gate")


@pytest.mark.parametrize(
    "tag", ["v1.0.0-beta.1", "v1.0.0-rc.0", "v01.0.0", "v1.0", "v1.0.0;exit 0", "poc-20261022.1"]
)
def test_invalid_or_ambiguous_tags_never_select_a_release_channel(policy, tag):
    with pytest.raises(ValueError):
        policy.release_version(tag)


def test_rc_and_stable_have_distinct_versions_and_channel_decisions(policy, tmp_path):
    assert policy.release_version("v1.0.0-rc.2") == ("1.0.0rc2", True)
    assert policy.release_version("v1.0.0") == ("1.0.0", False)
    (tmp_path / "src/aircooker").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="1.0.0rc2"\n')
    (tmp_path / "src/aircooker/__init__.py").write_text('__version__ = "1.0.0rc2"\n')
    assert policy.validate_metadata(tmp_path, "v1.0.0-rc.2")
    with pytest.raises(ValueError, match="must match"):
        policy.validate_metadata(tmp_path, "v1.0.0")


def test_open_missing_duplicate_or_unevidenced_gates_block_stable(policy):
    proof = {
        "schema_version": 1,
        "version": "1.0.0",
        "gates": [
            {"id": name, "status": "passed", "evidence": ["synthetic-acceptance-evidence"]}
            for name in sorted(policy.REQUIRED_GATES)
        ],
    }
    policy.validate_acceptance(proof, "v1.0.0")
    for field, value in [
        ("status", "open"),
        ("status", "partial"),
        ("evidence", []),
        ("evidence", [""]),
    ]:
        changed = deepcopy(proof)
        changed["gates"][0][field] = value
        with pytest.raises(ValueError):
            policy.validate_acceptance(changed, "v1.0.0")
    for rows in [proof["gates"][:-1], proof["gates"] + [proof["gates"][0]]]:
        with pytest.raises(ValueError):
            policy.validate_acceptance({**proof, "gates": rows}, "v1.0.0")
    with pytest.raises(ValueError):
        policy.validate_acceptance(proof, "v1.0.1")


def test_stable_retry_cannot_adopt_a_prerelease_or_mutable_image(policy):
    image, digest = "ghcr.io/cloudcookch/mealf-server", "sha256:" + "a" * 64
    release = {
        "tag_name": "v1.0.0",
        "draft": False,
        "prerelease": False,
        "body": f"Image: `{image}@{digest}`\n\nNotes",
    }
    assert policy.completed_digest(release, "v1.0.0", image, prerelease=False) == digest
    with pytest.raises(ValueError):
        policy.completed_digest({**release, "prerelease": True}, "v1.0.0", image, prerelease=False)


def test_release_install_asset_pins_verified_digest_and_preserves_deployment_options():
    assets = load("release_assets")
    template = (SCRIPTS.parent / "compose.preview.yaml").read_text()
    image, digest = "ghcr.io/cloudcookch/mealf-server", "sha256:" + "b" * 64
    rendered = assets.compose_for_image(template, image, digest)
    assert "${MEALF_IMAGE:-" + image + "@" + digest + "}" in rendered
    assert rendered.split("    restart:", 1)[1] == template.split("    restart:", 1)[1]
    for bad_image, bad_digest in [
        (image, "preview"),
        ("ghcr.io/other/other", digest),
        (image, digest + "\n"),
    ]:
        with pytest.raises(ValueError):
            assets.compose_for_image(template, bad_image, bad_digest)
    with pytest.raises(ValueError):
        assets.compose_for_image(template + template, image, digest)
