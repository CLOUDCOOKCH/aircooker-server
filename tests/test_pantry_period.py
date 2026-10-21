import hashlib
import json
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from aircooker.db import Database
from aircooker.models import Mutation
from aircooker.planning import shopping_projection
from aircooker.sync import apply_mutation


class MondayClock(datetime):
    @classmethod
    def now(cls, tz=None):
        # Sunday UTC, Monday in the configured Europe/Zurich household.
        value = datetime(2026, 10, 25, 23, 30, tzinfo=UTC)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)


def test_legacy_override_uses_household_week_and_replay_never_refreshes_it(
    harness, mutation, monkeypatch
):
    client, _, device, _ = harness
    monkeypatch.setattr("aircooker.sync.datetime", MondayClock)
    body = mutation(device, kind="pantry", payload={"name": "Salt", "include_this_week": True})
    first = client.post("/api/v1/sync/push", json={"mutations": [body]})
    assert first.status_code == 200, first.text
    record = client.get("/api/v1/pantry/" + body["entity_id"]).json()
    assert record["payload"]["include_week_start"] == "2026-10-26"
    # Emulate an immutable receipt written with the pre-period Pantry schema.
    legacy = Mutation.model_validate(body).model_dump(mode="json")
    legacy["payload"] = {"name": "Salt", "available": True, "include_this_week": True}
    fingerprint = hashlib.sha256(json.dumps(legacy, sort_keys=True).encode()).hexdigest()
    with client.app.state.database.transaction() as db:
        db.execute(
            "UPDATE mutation SET fingerprint=? WHERE id=?", (fingerprint, body["mutation_id"])
        )

    class NextWeek(MondayClock):
        @classmethod
        def now(cls, tz=None):
            value = datetime(2026, 11, 2, 12, tzinfo=UTC)
            return value.astimezone(tz) if tz else value.replace(tzinfo=None)

    monkeypatch.setattr("aircooker.sync.datetime", NextWeek)
    replay = client.post("/api/v1/sync/push", json={"mutations": [body]})
    assert replay.json() == first.json()
    assert client.get("/api/v1/pantry/" + body["entity_id"]).json() == record


def test_period_override_expires_and_offline_date_is_not_replaced_by_arrival_clock(
    harness, mutation
):
    client, app, device, _ = harness
    recipe = mutation(
        device,
        payload={
            "title": "Soup",
            "servings": "2",
            "ingredients": [{"id": str(uuid4()), "name": "Salt", "quantity": "1", "unit": "g"}],
        },
    )
    meal = mutation(
        device,
        kind="meal",
        payload={
            "recipe_id": recipe["entity_id"],
            "date": "2026-10-19",
            "category": "dinner",
            "servings": "2",
            "recurrence": {"until": "2026-11-02"},
        },
    )
    pantry = mutation(
        device,
        kind="pantry",
        payload={"name": "Salt", "include_this_week": True, "include_week_start": "2026-10-26"},
    )
    for body in (recipe, meal, pantry):
        response = client.post("/api/v1/sync/push", json={"mutations": [body]})
        assert response.status_code == 200, response.text
    with app.state.database.connect() as db:
        assert not shopping_projection(db, date(2026, 10, 19))
        assert len(shopping_projection(db, date(2026, 10, 26))) == 1
        assert not shopping_projection(db, date(2026, 11, 2))
        assert (
            db.execute("SELECT include_week_start FROM pantry_item").fetchone()[0] == "2026-10-26"
        )
    invalid = mutation(
        device,
        kind="pantry",
        payload={"name": "Oil", "include_this_week": True, "include_week_start": "2026-10-27"},
    )
    assert client.post("/api/v1/sync/push", json={"mutations": [invalid]}).status_code == 422


def test_undated_legacy_restore_does_not_reactivate_a_temporary_override(harness, mutation):
    _, app, device, _ = harness
    old = Mutation.model_validate(
        mutation(device, kind="pantry", payload={"name": "Salt", "include_this_week": True})
    )
    with app.state.database.transaction() as db:
        apply_mutation(db, old, device, restoring=True)
    with app.state.database.connect() as db:
        saved = json.loads(
            db.execute("SELECT payload FROM entity WHERE kind='pantry'").fetchone()[0]
        )
    assert saved["include_this_week"] is False and saved["include_week_start"] is None


def legacy_database(root: Path):
    directory = root / "database"
    directory.mkdir()
    connection = sqlite3.connect(directory / "aircooker.sqlite3")
    connection.execute("CREATE TABLE schema_migration(version TEXT PRIMARY KEY)")
    for script in sorted(Path("src/aircooker/migrations").glob("*.sql")):
        if script.name >= "006_pantry_period.sql":
            break
        connection.executescript(script.read_text())
        connection.execute("INSERT INTO schema_migration VALUES (?)", (script.name,))
        connection.commit()
    connection.execute(
        "INSERT INTO household VALUES (1,?,?,?,?,?,?)",
        ("Kitchen", "Europe/Zurich", "en", "cook", "unused hash", str(uuid4())),
    )
    identity = str(uuid4())
    raw = json.dumps({"name": "Salt", "available": True, "include_this_week": True})
    stamp = "2026-10-25T23:30:00+00:00"
    connection.execute("INSERT INTO entity VALUES (?,?,1,0,?,?)", ("pantry", identity, raw, stamp))
    connection.execute(
        "INSERT INTO change_log(sequence,kind,entity_id,deleted,payload,updated_at,commit_token) VALUES (1,?,?,0,?,?,?)",
        ("pantry", identity, raw, stamp, "a" * 32),
    )
    connection.execute("INSERT INTO pantry_item VALUES (?,?,1,1,0)", (identity, "Salt"))
    connection.commit()
    connection.close()
    return identity, raw


def test_migration_publishes_new_revisions_without_rewriting_history_and_is_repeatable(tmp_path):
    identity, raw = legacy_database(tmp_path)
    database = Database(tmp_path)
    with database.connect() as db:
        previous = db.execute("SELECT * FROM change_log WHERE sequence=1").fetchone()
        assert previous["payload"] == raw and previous["commit_token"] == "a" * 32
        current = db.execute("SELECT * FROM entity WHERE id=?", (identity,)).fetchone()
        assert (
            current["revision"] == 2
            and json.loads(current["payload"])["include_week_start"] == "2026-10-26"
        )
        assert (
            db.execute("SELECT include_week_start FROM pantry_item").fetchone()[0] == "2026-10-26"
        )
    again = Database(tmp_path)
    with again.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM change_log").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM device").fetchone()[0] == 1


def test_failed_backfill_rolls_back_schema_new_commits_and_migration_marker(tmp_path, monkeypatch):
    legacy_database(tmp_path)
    import aircooker.data_migrations as migrations

    original = migrations.apply_mutation

    def fail_after_write(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("Injected migration interruption")

    with monkeypatch.context() as patch:
        patch.setattr(migrations, "apply_mutation", fail_after_write)
        with pytest.raises(RuntimeError, match="Injected"):
            Database(tmp_path)
    connection = sqlite3.connect(tmp_path / "database/aircooker.sqlite3")
    assert connection.execute("SELECT COUNT(*) FROM change_log").fetchone()[0] == 1
    assert (
        connection.execute(
            "SELECT COUNT(*) FROM schema_migration WHERE version='006_pantry_period.sql'"
        ).fetchone()[0]
        == 0
    )
    assert "include_week_start" not in [
        row[1] for row in connection.execute("PRAGMA table_info(pantry_item)")
    ]
    connection.close()
    database = Database(tmp_path)
    with database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM change_log").fetchone()[0] == 2
