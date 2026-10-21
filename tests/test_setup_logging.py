import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from aircooker.app import create_app


@pytest.fixture(autouse=True)
def default_logging(monkeypatch):
    monkeypatch.delenv("LOG_SETUP_TOKEN", raising=False)


def test_setup_token_logs_only_at_startup_and_is_the_working_bootstrap_token(tmp_path, capsys):
    app = create_app(tmp_path, False)
    assert capsys.readouterr().out == ""  # Schema/factory tools must not print tokens.
    with TestClient(app) as client:
        lines = capsys.readouterr().out.splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["event"] == "setup_required"
        token_file = tmp_path / "config/setup-token"
        assert entry["setup_token"] == token_file.read_text()
        assert token_file.stat().st_mode & 0o777 == 0o600
        body = {
            "name": "Setup logging test",
            "username": "cook",
            "password": "synthetic private bootstrap password",
            "device_id": str(uuid4()),
        }
        assert client.get("/api/v1/system/info").status_code == 200
        assert client.post("/api/v1/setup", json=body).status_code == 403
        response = client.post(
            "/api/v1/setup", json=body, headers={"X-Setup-Token": entry["setup_token"]}
        )
        assert response.status_code == 201
        assert response.json()["access_token"] and response.json()["refresh_token"]
        assert not token_file.exists()
        assert capsys.readouterr().out == ""  # No request, password or session logging.


def test_unconfigured_restart_logs_existing_token_without_rotating_it(tmp_path, capsys):
    logged = []
    for _ in range(2):
        app = create_app(tmp_path, False)
        assert capsys.readouterr().out == ""
        with TestClient(app):
            output = capsys.readouterr().out.splitlines()
            assert len(output) == 1
            logged.append(json.loads(output[0])["setup_token"])
    assert logged[0] == logged[1] == (tmp_path / "config/setup-token").read_text()


def test_startup_rechecks_configured_state_and_never_logs_a_stale_token(tmp_path, capsys):
    app = create_app(tmp_path, False)
    constructed_before_setup = create_app(tmp_path, False)
    with TestClient(app) as client:
        token = json.loads(capsys.readouterr().out)["setup_token"]
        assert (
            client.post(
                "/api/v1/setup",
                headers={"X-Setup-Token": token},
                json={
                    "name": "Already configured",
                    "username": "cook",
                    "password": "synthetic configured password",
                    "device_id": str(uuid4()),
                },
            ).status_code
            == 201
        )
    assert capsys.readouterr().out == ""
    # Even a leftover file and a previously constructed app must not disclose a token.
    (tmp_path / "config/setup-token").write_text("synthetic stale token must never be logged")
    for started in (constructed_before_setup, create_app(tmp_path, False)):
        with TestClient(started):
            assert capsys.readouterr().out == ""


def test_operator_can_disable_token_logging_without_disabling_setup(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LOG_SETUP_TOKEN", "false")
    app = create_app(tmp_path, False)
    with TestClient(app) as client:
        assert capsys.readouterr().out == ""
        assert (tmp_path / "config/setup-token").read_text()
        assert client.get("/api/v1/system/info").json()["configured"] is False
