import runpy

import pytest


def test_supplemental_notice_is_exactly_version_and_licence_bound():
    notice = runpy.run_path("scripts/license_inventory.py")["supplemental_notice"]
    assert (
        notice("http-ece", "1.2.1", "MIT")[0]["path"] == "mealf:attributions/http-ece-1.2.1.LICENSE"
    )
    assert notice("unreviewed-package", "1", "MIT") == []
    with pytest.raises(SystemExit, match="version/licence mismatch"):
        notice("http-ece", "1.2.2", "MIT")


def test_missing_or_modified_supplement_cannot_pass_inventory(tmp_path, monkeypatch):
    notice = runpy.run_path("scripts/license_inventory.py")["supplemental_notice"]
    root = tmp_path / "attributions"
    root.mkdir()
    (root / "http-ece-1.2.1.LICENSE").write_text("Modified or empty notice")
    monkeypatch.setattr("importlib.resources.files", lambda package: tmp_path)
    with pytest.raises(SystemExit, match="checksum mismatch"):
        notice("http-ece", "1.2.1", "MIT")
