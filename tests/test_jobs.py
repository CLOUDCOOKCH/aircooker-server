import time

from mealf.db import Database
from mealf.jobs import claim, enqueue, finish


def test_queue_survives_restart_and_deduplicates(tmp_path):
    database = Database(tmp_path)
    with database.transaction() as db:
        enqueue(db, "test", "one", {"a": 1})
        enqueue(db, "test", "one", {"a": 2})
    restarted = Database(tmp_path)
    job = claim(restarted)
    assert job["generation"] == 2
    assert claim(restarted) is None
    assert finish(restarted, job)
    assert claim(restarted) is None


def test_lease_recovery_and_stale_worker_fencing(tmp_path):
    database = Database(tmp_path)
    with database.transaction() as db:
        enqueue(db, "test", "one", {})
    old = claim(database, lease_seconds=-1)
    new = claim(database)
    assert new["id"] == old["id"] and new["lease_token"] != old["lease_token"]
    assert not finish(database, old)
    assert finish(database, new)


def test_running_job_new_generation_is_not_lost(tmp_path):
    database = Database(tmp_path)
    with database.transaction() as db:
        enqueue(db, "test", "one", {})
    old = claim(database)
    with database.transaction() as db:
        enqueue(db, "test", "one", {"new": True})
    finish(database, old)
    assert claim(database)["generation"] == 2


def test_retry_backoff_and_failure(tmp_path):
    database = Database(tmp_path)
    with database.transaction() as db:
        enqueue(db, "test", "one", {})
    job = claim(database)
    finish(database, job, "temporary")
    assert claim(database) is None
    with database.connect() as db:
        row = db.execute("SELECT * FROM background_job").fetchone()
        assert row["state"] == "queued" and row["error_code"] == "temporary"
        assert row["available_at"] > time.time()


def test_terminal_failure_preserves_actual_attempt_count(tmp_path):
    database = Database(tmp_path)
    with database.transaction() as db:
        enqueue(db, "bring.verify", "one", {})
    job = claim(database)
    finish(database, job, "bring_uuid_not_supported", terminal=True)
    with database.connect() as db:
        row = db.execute("SELECT * FROM background_job").fetchone()
        assert row["state"] == "failed" and row["attempts"] == 1
    assert claim(database) is None


def test_newer_generation_survives_terminal_failure_of_running_attempt(tmp_path):
    database = Database(tmp_path)
    with database.transaction() as db:
        enqueue(db, "test", "one", {"old": True})
    job = claim(database)
    with database.transaction() as db:
        enqueue(db, "test", "one", {"new": True})
    finish(database, job, "permanent_old_failure", terminal=True)
    assert claim(database)["generation"] == 2
