import json
import os
import subprocess
import sys
import time
from datetime import date, timedelta
from importlib.resources import files
from uuid import uuid4

import pytest

from aircooker.db import Database
from aircooker.errors import DomainError
from aircooker.import_receipts import fingerprint
from aircooker.jobs import claim, enqueue, finish
from aircooker.retention import BATCH, DAY, cleanup_database, cleanup_startup_transfers


def preview_import(harness):
    client, app, _, _ = harness
    body = {
        "request_id": str(uuid4()),
        "text": '<!-- private synthetic source marker --><script type="application/ld+json">'
        + json.dumps(
            {
                "@type": "Recipe",
                "name": "Reviewed soup",
                "recipeYield": "2",
                "recipeIngredient": ["200 g carrots"],
                "recipeInstructions": ["Simmer until tender."],
            }
        )
        + "</script>",
    }
    response = client.post("/api/v1/imports", json=body)
    assert response.status_code == 202, response.text
    job = claim(app.state.database)
    assert job and job["kind"] == "recipe.import"
    app.state.process_job(job)
    assert finish(app.state.database, job)
    draft = client.get("/api/v1/imports/" + body["request_id"]).json()
    assert draft["state"] == "preview"
    return body, job, draft


def confirm(harness, mutation, body, draft):
    client, _, device, _ = harness
    change = mutation(device, payload=draft["recipe"])
    response = client.post("/api/v1/imports/" + body["request_id"] + "/confirm", json=change)
    assert response.status_code == 200, response.text
    return change, response.json()


def test_terminal_import_text_can_be_pruned_without_breaking_request_or_confirmation_replay(
    harness, mutation
):
    client, app, device, _ = harness
    body, job, draft = preview_import(harness)
    change, receipt = confirm(harness, mutation, body, draft)
    proof = client.get("/api/v1/sync/state").json()
    result = cleanup_database(app.state.database, now=time.time() + 31 * DAY)
    assert result["import_previews"] == 1 and result["terminal_jobs"] == 1
    after = client.get("/api/v1/imports/" + body["request_id"]).json()
    assert after["state"] == "confirmed" and after["recipe"] is None
    assert "request_fingerprint" not in after and "finished_at" not in after
    replay = client.post("/api/v1/imports", json=body)
    assert replay.status_code == 202 and replay.json()["state"] == "confirmed"
    assert (
        client.post("/api/v1/imports", json={**body, "text": "changed source"}).status_code == 409
    )
    assert (
        client.post("/api/v1/imports/" + body["request_id"] + "/confirm", json=change).json()
        == receipt
    )
    assert client.get("/api/v1/sync/state").json() == proof
    assert (
        client.get("/api/v1/recipes/" + change["entity_id"]).json()["payload"]["title"]
        == "Reviewed soup"
    )
    with app.state.database.connect() as db:
        assert not db.execute("SELECT 1 FROM background_job WHERE id=?", (job["id"],)).fetchone()
        assert db.execute(
            "SELECT request_fingerprint FROM import_draft WHERE id=?", (body["request_id"],)
        ).fetchone()[0]
        assert "private synthetic source marker" not in json.dumps(
            [dict(row) for row in db.execute("SELECT payload FROM background_job")]
        )

    edit = mutation(
        device,
        entity_id=change["entity_id"],
        base=receipt["revision"],
        payload={**draft["recipe"], "notes": "Offline edit after source retention"},
    )
    response = client.post("/api/v1/sync/push", json={"mutations": [edit]})
    assert response.status_code == 200, response.text


def test_cleanup_keeps_pending_failed_and_unknown_legacy_imports_and_sync_proofs(harness, mutation):
    client, app, _, _ = harness
    bodies = []
    for _ in range(4):
        body, job, draft = preview_import(harness)
        bodies.append(body)
        if len(bodies) == 1:
            client.delete("/api/v1/imports/" + body["request_id"])
        elif len(bodies) == 2:
            # Pending preview is user work, even when very old.
            pass
        elif len(bodies) == 3:
            with app.state.database.transaction() as db:
                db.execute(
                    "UPDATE import_draft SET state='needs_input',error_code='source_unavailable' WHERE id=?",
                    (body["request_id"],),
                )
                db.execute("UPDATE background_job SET state='failed' WHERE id=?", (job["id"],))
        else:
            client.delete("/api/v1/imports/" + body["request_id"])
            with app.state.database.transaction() as db:
                db.execute(
                    "UPDATE import_draft SET request_fingerprint=NULL WHERE id=?",
                    (body["request_id"],),
                )
    before = client.get("/api/v1/sync/state").json()
    result = cleanup_database(app.state.database, now=time.time() + 31 * DAY)
    assert result["terminal_jobs"] == 1
    assert client.get("/api/v1/imports/" + bodies[1]["request_id"]).json()["recipe"]
    with app.state.database.connect() as db:
        assert (
            db.execute('SELECT COUNT(*) FROM background_job WHERE kind="recipe.import"').fetchone()[
                0
            ]
            == 3
        )
        assert db.execute("SELECT COUNT(*) FROM import_draft").fetchone()[0] == 4
    assert client.get("/api/v1/imports/" + bodies[2]["request_id"]).json()["state"] == "needs_input"
    assert client.get("/api/v1/sync/state").json() == before


def test_maintenance_is_bounded_and_dry_run_does_not_mutate(harness):
    _, app, _, _ = harness
    now = time.time()
    with app.state.database.transaction() as db:
        db.executemany(
            "INSERT INTO audit_event(code,created_at) VALUES (?,?)",
            [("synthetic_old", now - 91 * DAY)] * (BATCH + 5),
        )
        db.execute("INSERT INTO rate_limit VALUES (?,?,?)", ("expired_old", 1, now - 2 * DAY))
        db.execute("INSERT INTO rate_limit VALUES (?,?,?)", ("current", 10, now + DAY))
    report = cleanup_database(app.state.database, now=now, dry_run=True)
    assert report["audit_event"] == BATCH and report["rate_limit"] == 1
    with app.state.database.connect() as db:
        assert (
            db.execute('SELECT COUNT(*) FROM audit_event WHERE code="synthetic_old"').fetchone()[0]
            == BATCH + 5
        )
    assert cleanup_database(app.state.database, now=now)["audit_event"] == BATCH
    assert cleanup_database(app.state.database, now=now)["audit_event"] == 5
    with app.state.database.connect() as db:
        assert db.execute('SELECT count FROM rate_limit WHERE key="current"').fetchone()[0] == 10


def seed_subscription(db, device, session_id):
    sid = str(uuid4())
    db.execute(
        """INSERT INTO push_subscription(id,device_id,session_id,endpoint_hash,credentials,preferences,language,updated_at)
      VALUES (?,?,?,?,?,?,?,?)""",
        (
            sid,
            device,
            session_id,
            str(uuid4()),
            "synthetic-unused-credentials",
            json.dumps(
                {"enabled": True, "breakfast": "07:30", "lunch": "12:00", "dinner": "18:00"}
            ),
            "en",
            time.time(),
        ),
    )
    return sid


def test_only_long_expired_unreferenced_sessions_are_removed_and_devices_are_retained(harness):
    client, app, device, tokens = harness
    now = time.time()
    peers = []
    for _ in range(2):
        peer = str(uuid4())
        session = client.post(
            "/api/v1/auth/login",
            json={"username": "cook", "password": "a strong test password", "device_id": peer},
        ).json()
        peers.append((peer, session))
    with app.state.database.transaction() as db:
        for _, session in peers:
            db.execute(
                "UPDATE session SET refresh_expires=? WHERE id=?",
                (now - 91 * DAY, session["session_id"]),
            )
            db.execute(
                "INSERT INTO refresh_history VALUES (?,?)", (str(uuid4()), session["session_id"])
            )
        seed_subscription(db, peers[1][0], peers[1][1]["session_id"])
    result = cleanup_database(app.state.database, now=now)
    assert result["expired_sessions"] == 1
    with app.state.database.connect() as db:
        assert not db.execute(
            "SELECT 1 FROM session WHERE id=?", (peers[0][1]["session_id"],)
        ).fetchone()
        assert db.execute("SELECT 1 FROM device WHERE id=?", (peers[0][0],)).fetchone()
        assert db.execute(
            "SELECT 1 FROM session WHERE id=?", (peers[1][1]["session_id"],)
        ).fetchone()
        assert not db.execute(
            "SELECT 1 FROM refresh_history WHERE session_id=?", (peers[0][1]["session_id"],)
        ).fetchone()
    assert client.get("/api/v1/recipes").status_code == 200


def test_notification_receipts_and_test_request_replay_survive_job_cleanup(harness):
    _, app, device, tokens = harness
    now = time.time()
    day = (date.today() - timedelta(days=31)).isoformat()
    with app.state.database.transaction() as db:
        sid = seed_subscription(db, device, tokens["session_id"])
        db.execute(
            "INSERT INTO push_delivery VALUES (?,?,?,?)", (sid, day, "dinner", now - 31 * DAY)
        )
        test_id = str(uuid4())
        keys = [
            ("notification.meal", f"push.meal:{sid}:{day}:dinner", "done"),
            ("notification.test", f"push.test:{sid}:{test_id}", "done"),
            ("notification.test", f"push.test:{uuid4()}:{uuid4()}", "done"),
            ("notification.test", f"push.test:{sid}:{uuid4()}", "queued"),
            ("notification.test", f"push.test:{sid}:{uuid4()}", "failed"),
        ]
        keys.extend(
            [
                ("shopping.reconcile", "shopping.current", "done"),
                ("future.unknown", "future.unknown", "done"),
            ]
        )
        db.execute(
            "INSERT INTO bring_owned_item VALUES (?,?,?,?,?,?,?,?,?)",
            (
                day,
                "requirement",
                str(uuid4()),
                str(uuid4()),
                "Carrots",
                "200 g",
                "purchased",
                "200 g",
                now - 31 * DAY,
            ),
        )
        for kind, key, state in keys:
            enqueue(db, kind, key, {"subscription_id": sid})
            db.execute(
                "UPDATE background_job SET state=?,available_at=? WHERE dedupe_key=?",
                (state, now - 31 * DAY, key),
            )
    assert cleanup_database(app.state.database, now=now)["terminal_jobs"] == 2
    app.state.reminders.queue_test(device, test_id)
    with app.state.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM background_job").fetchone()[0] == 5
        assert db.execute("SELECT COUNT(*) FROM push_delivery").fetchone()[0] == 1

        assert db.execute("SELECT state FROM bring_owned_item").fetchone()[0] == "purchased"


def test_startup_prunes_only_stale_regular_transfer_files(tmp_path):
    database = Database(tmp_path)
    outside = tmp_path / "keep-private.txt"
    outside.write_text("synthetic external file")
    stale = tmp_path / "jobs/.export-synthetic.zip"
    stale.write_text("old transfer")
    recent = tmp_path / "jobs/.restore-recent.zip"
    recent.write_text("recent transfer")
    other = tmp_path / "jobs/backup.zip"
    other.write_text("user-managed file")
    linked = tmp_path / "jobs/.export-linked.zip"
    linked.symlink_to(outside)
    old = time.time() - 2 * DAY
    os.utime(stale, (old, old))
    os.utime(other, (old, old))
    os.utime(linked, (old, old), follow_symlinks=False)
    assert cleanup_startup_transfers(database.root) == 1
    assert (
        not stale.exists()
        and recent.exists()
        and other.exists()
        and linked.is_symlink()
        and outside.read_text() == "synthetic external file"
    )


def legacy_database(root, monkeypatch):
    resources = root / "old-package"
    (resources / "migrations").mkdir(parents=True)
    for source in files("aircooker").joinpath("migrations").iterdir():
        if source.name.endswith(".sql") and source.name < "009":
            (resources / "migrations" / source.name).write_text(source.read_text())
    with monkeypatch.context() as patch:
        patch.setattr("aircooker.db.files", lambda package: resources)
        database = Database(root / "data")
    payload = {
        "id": str(uuid4()),
        "text": "synthetic old source",
        "source_url": None,
        "use_ai": False,
        "consent_external_ai": False,
    }
    with database.transaction() as db:
        db.execute(
            "INSERT INTO import_draft VALUES (?,?,?,'cancelled',NULL,'[]',NULL,NULL,0)",
            (payload["id"], None, "supplied_text"),
        )
        enqueue(db, "recipe.import", "import:" + payload["id"], payload)
        db.execute("UPDATE background_job SET state='done'")
    return database, payload


def test_upgrade_backfills_old_request_receipts_with_a_fresh_completion_grace_period(
    tmp_path, monkeypatch
):
    old, body = legacy_database(tmp_path, monkeypatch)
    before = time.time()
    updated = Database(old.root)
    with updated.connect() as db:
        row = db.execute("SELECT * FROM import_draft").fetchone()
        assert row["request_fingerprint"] == fingerprint(body) and row["finished_at"] >= before
        completion = row["finished_at"]
    assert cleanup_database(updated)["terminal_jobs"] == 0
    assert cleanup_database(updated, now=time.time() + 31 * DAY)["terminal_jobs"] == 1
    Database(updated.root)
    with updated.connect() as db:
        assert db.execute("SELECT finished_at FROM import_draft").fetchone()[0] == completion


def test_failed_data_backfill_rolls_back_schema_and_migration_marker(tmp_path, monkeypatch):
    old, _ = legacy_database(tmp_path, monkeypatch)

    def broken(db):
        db.execute("UPDATE import_draft SET state='confirmed'")
        raise RuntimeError("synthetic migration interruption")

    with monkeypatch.context() as patch:
        patch.setattr("aircooker.import_receipts.backfill", broken)
        with pytest.raises(RuntimeError, match="synthetic migration interruption"):
            Database(old.root)
    with old.connect() as db:
        assert "request_fingerprint" not in [
            row[1] for row in db.execute("PRAGMA table_info(import_draft)")
        ]
        assert not db.execute(
            "SELECT 1 FROM schema_migration WHERE version='009_import_retention.sql'"
        ).fetchone()
        assert db.execute("SELECT state FROM import_draft").fetchone()[0] == "cancelled"
    Database(old.root)


@pytest.mark.parametrize("outcome", ["success", "failure"])
def test_import_worker_cannot_downgrade_an_explicitly_confirmed_preview(
    harness, mutation, monkeypatch, outcome
):
    from aircooker.importing import extract

    client, app, _, _ = harness
    body, job, draft = preview_import(harness)

    def finish_during_extraction(*args):
        result = extract(*args)
        confirm(harness, mutation, body, draft)
        if outcome == "failure":
            raise DomainError("synthetic_extraction_failure", 422)
        return result

    monkeypatch.setattr("aircooker.app.extract", finish_during_extraction)
    app.state.process_job(job)
    assert client.get("/api/v1/imports/" + body["request_id"]).json()["state"] == "confirmed"

    def forbidden(*args):
        raise AssertionError("A confirmed import was extracted again")

    monkeypatch.setattr("aircooker.app.extract", forbidden)
    app.state.process_job(job)
    assert len(client.get("/api/v1/recipes").json()["items"]) == 1


def test_packaged_cli_cleanup_dry_run_and_apply_keep_output_redacted(harness):
    _, app, _, _ = harness
    with app.state.database.transaction() as db:
        db.execute(
            "INSERT INTO audit_event(code,created_at) VALUES (?,?)",
            ("synthetic-private-audit-body", time.time() - 91 * DAY),
        )
    environment = {**os.environ, "DATA_DIR": str(app.state.database.root), "PYTHONPATH": "src"}
    command = [sys.executable, "-m", "aircooker.cli", "cleanup"]
    preview = subprocess.run(
        command + ["--dry-run"], env=environment, capture_output=True, text=True, check=True
    )
    assert json.loads(preview.stdout)["counts"]["audit_event"] == 1
    assert "synthetic-private-audit-body" not in preview.stdout
    applied = subprocess.run(command, env=environment, capture_output=True, text=True, check=True)
    assert json.loads(applied.stdout)["counts"]["audit_event"] == 1
    assert (
        json.loads(
            subprocess.run(
                command + ["--dry-run"], env=environment, capture_output=True, text=True, check=True
            ).stdout
        )["counts"]["audit_event"]
        == 0
    )

    destination = app.state.database.root / "backups/should-not-exist.sqlite"
    invalid = subprocess.run(
        [
            sys.executable,
            "-m",
            "aircooker.cli",
            "backup",
            "--dry-run",
            "--output",
            str(destination),
        ],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert invalid.returncode == 2 and not destination.exists()


def test_legacy_backfill_streams_multiple_batches_and_keeps_unrecognised_receipts(
    tmp_path, monkeypatch
):
    old, original = legacy_database(tmp_path, monkeypatch)
    with old.transaction() as db:
        for _ in range(205):
            body = {**original, "id": str(uuid4())}
            db.execute(
                "INSERT INTO import_draft VALUES (?,?,?,'cancelled',NULL,'[]',NULL,NULL,0)",
                (body["id"], None, "supplied_text"),
            )
            enqueue(db, "recipe.import", "import:" + body["id"], body)
        unknown = str(uuid4())
        db.execute(
            "INSERT INTO import_draft VALUES (?,?,?,'cancelled',NULL,'[]',NULL,NULL,0)",
            (unknown, None, "supplied_text"),
        )
        enqueue(db, "recipe.import", "import:" + unknown, {"text": "unknown legacy shape"})
        db.execute("UPDATE background_job SET state='done'")
    updated = Database(old.root)
    with updated.connect() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM import_draft WHERE request_fingerprint IS NOT NULL"
            ).fetchone()[0]
            == 206
        )
        assert (
            db.execute(
                "SELECT request_fingerprint FROM import_draft WHERE id=?", (unknown,)
            ).fetchone()[0]
            is None
        )
    assert cleanup_database(updated, now=time.time() + 31 * DAY)["terminal_jobs"] == 206
    with updated.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM background_job").fetchone()[0] == 1


def test_cleanup_failure_is_redacted_and_does_not_stop_the_durable_worker(
    tmp_path, monkeypatch, caplog
):
    from fastapi.testclient import TestClient

    from aircooker.app import create_app

    def failed_cleanup(*args, **kwargs):
        raise RuntimeError("private synthetic cleanup detail")

    monkeypatch.setattr("aircooker.app.cleanup_database", failed_cleanup)
    app = create_app(tmp_path, run_worker=True)
    with TestClient(app) as client:
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            assert client.get("/api/v1/system/health").status_code == 200
            with app.state.database.connect() as db:
                done = db.execute(
                    "SELECT 1 FROM background_job WHERE dedupe_key='shopping.current' AND state='done'"
                ).fetchone()
            if done:
                break
            time.sleep(0.01)
        assert done
    assert "maintenance_cleanup_failed" in caplog.text
    assert "private synthetic cleanup detail" not in caplog.text
