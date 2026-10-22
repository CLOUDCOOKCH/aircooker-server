"""Real SQLite quota failures preserve state and the durable worker can recover."""

import logging
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

import aircooker.app as application
from aircooker.db import Database


@pytest.mark.parametrize("value", ["not-a-size", "0", "-1", str(65 * 1024**3)])
def test_invalid_database_limit_fails_startup_explicitly(tmp_path, monkeypatch, value):
    monkeypatch.setenv("DATABASE_MAX_BYTES", value)
    with pytest.raises(ValueError, match="DATABASE_MAX_BYTES"):
        Database(tmp_path)


def test_database_quota_rolls_back_mutation_and_allows_identical_retry(harness, mutation):
    client, app, device, _ = harness
    database = app.state.database
    database.max_bytes = 1024**2
    before = client.get("/api/v1/sync/state").json()
    change = mutation(
        device,
        payload={
            "title": "Synthetic oversized snapshot",
            "servings": "2",
            "ingredients": [],
            "steps": ["x" * 5000 for _ in range(180)],
        },
    )
    response = client.post("/api/v1/sync/push", json={"mutations": [change]})
    assert response.status_code == 503, response.text
    assert response.json() == {"error": {"code": "storage_unavailable"}}
    assert client.get("/api/v1/sync/state").json() == before
    with database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM entity").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM mutation").fetchone()[0] == 0
        assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        assert db.execute("PRAGMA max_page_count").fetchone()[0] <= 1024**2 // 4096
    database.max_bytes = 16 * 1024**2
    response = client.post("/api/v1/sync/push", json={"mutations": [change]})
    assert response.status_code == 200, response.text
    assert client.post("/api/v1/sync/push", json={"mutations": [change]}).json() == response.json()
    assert len(client.get("/api/v1/recipes").json()["items"]) == 1


def test_cap_is_applied_after_restart_without_truncating_existing_data(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_MAX_BYTES", str(8 * 1024**2))
    original = Database(tmp_path)
    with original.transaction() as db:
        db.execute("CREATE TABLE synthetic_quota_probe (content BLOB)")
        db.execute("INSERT INTO synthetic_quota_probe VALUES (?)", (b"a" * 2 * 1024**2,))
    monkeypatch.setenv("DATABASE_MAX_BYTES", str(1024**2))
    reopened = Database(tmp_path)
    with reopened.connect() as db:
        assert (
            db.execute("SELECT length(content) FROM synthetic_quota_probe").fetchone()[0]
            == 2 * 1024**2
        )
        assert (
            db.execute("PRAGMA max_page_count").fetchone()[0]
            == db.execute("PRAGMA page_count").fetchone()[0]
        )
        assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        with pytest.raises(sqlite3.OperationalError, match="full"):
            db.execute("INSERT INTO synthetic_quota_probe VALUES (?)", (b"b" * 1024**2,))


def test_transient_claim_failure_does_not_kill_background_worker(tmp_path, monkeypatch, caplog):
    real_claim = application.claim
    calls = []

    def claim(database):
        calls.append(True)
        if len(calls) == 1:
            raise sqlite3.OperationalError("synthetic unavailable storage")
        return real_claim(database)

    monkeypatch.setattr(application, "claim", claim)
    monkeypatch.setenv("LOG_SETUP_TOKEN", "false")
    app = application.create_app(tmp_path)
    with caplog.at_level(logging.WARNING), TestClient(app) as client:
        deadline = time.monotonic() + 5
        while len(calls) < 2 and time.monotonic() < deadline:
            time.sleep(0.02)
        assert len(calls) >= 2
        assert client.get("/api/v1/system/health").status_code == 200
    assert '"event":"worker_retry"' in caplog.text
    assert "synthetic unavailable storage" not in caplog.text
