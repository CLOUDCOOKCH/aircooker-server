import sqlite3
from uuid import uuid4

from mealf.db import Database


def push(c, *items, checkpoint=None):
    return c.post(
        "/api/v1/sync/push",
        json={"mutations": list(items), **({"checkpoint": checkpoint} if checkpoint else {})},
    )


def anchor(c):
    state = c.get("/api/v1/sync/state").json()
    return {"cursor": state["cursor"], "token": state["token"]}


def backup(database, path):
    with database.connect() as source, sqlite3.connect(path) as target:
        source.backup(target)


def restore(database, path):
    with sqlite3.connect(path) as source, database.connect() as target:
        source.backup(target)


def test_proofs_are_stable_across_restart_and_each_commit_is_unique(harness, mutation):
    c, app, device, _ = harness
    assert anchor(c) == {"cursor": 0, "token": "root"}
    first = mutation(device)
    assert push(c, first).status_code == 200
    prior = anchor(c)
    assert len(prior["token"]) == 32
    assert push(c, first).status_code == 200  # Replay cannot generate another proof.
    assert anchor(c) == prior
    assert push(c, mutation(device)).status_code == 200
    state = c.get("/api/v1/sync/state", params={"cursor": prior["cursor"]}).json()
    assert state["requested_token"] == prior["token"] and state["token"] != prior["token"]
    assert c.get("/api/v1/sync/pull").json()["cursor_token"] == state["token"]
    Database(app.state.database.root)
    assert anchor(c)["token"] == state["token"]


def test_same_revision_reused_after_restore_has_a_different_proof(harness, mutation, tmp_path):
    c, app, device, _ = harness
    assert push(c, mutation(device)).status_code == 200
    snapshot = tmp_path / "consistent.sqlite"
    backup(app.state.database, snapshot)
    assert push(c, mutation(device)).status_code == 200
    lost_branch = anchor(c)
    restore(app.state.database, snapshot)
    assert push(c, mutation(device)).status_code == 200
    state = c.get("/api/v1/sync/state", params={"cursor": lost_branch["cursor"]}).json()
    assert state["cursor"] == lost_branch["cursor"]
    assert state["requested_token"] != lost_branch["token"]
    stale_write = mutation(device)
    rejected = push(c, stale_write, checkpoint=lost_branch)
    assert (
        rejected.status_code == 409 and rejected.json()["error"]["code"] == "sync_history_changed"
    )
    assert c.get("/api/v1/recipes/" + stale_write["entity_id"]).status_code == 404
    assert c.get("/api/v1/sync/snapshot", params=lost_branch).status_code == 409


def test_cursor_beyond_restored_head_is_reported_without_writes(harness, mutation, tmp_path):
    c, app, device, _ = harness
    snapshot = tmp_path / "empty.sqlite"
    backup(app.state.database, snapshot)
    assert push(c, mutation(device)).status_code == 200
    prior = anchor(c)
    restore(app.state.database, snapshot)
    state = c.get("/api/v1/sync/state", params={"cursor": prior["cursor"]}).json()
    assert state["cursor"] == 0 and state["requested_token"] is None
    assert push(c, mutation(device), checkpoint=prior).status_code == 409


def test_snapshot_pages_remain_at_anchor_during_concurrent_writes(harness, mutation):
    c, _, device, _ = harness
    items = [mutation(device) for _ in range(4)]
    for item in items:
        assert push(c, item).status_code == 200
    checkpoint = anchor(c)
    first = c.get("/api/v1/sync/snapshot", params={**checkpoint, "limit": 2}).json()
    assert len(first["changes"]) == 2 and first["next_after"]
    changed = mutation(device, entity_id=items[2]["entity_id"], payload={"title": "Later revision"})
    assert push(c, changed).status_code == 200
    assert (
        push(c, mutation(device, entity_id=items[3]["entity_id"], operation="delete")).status_code
        == 200
    )
    assert push(c, mutation(device)).status_code == 200
    second = c.get(
        "/api/v1/sync/snapshot", params={**checkpoint, "limit": 2, "after": first["next_after"]}
    ).json()
    all_rows = first["changes"] + second["changes"]
    assert second["next_after"] is None
    assert {r["entity_id"] for r in all_rows} == {m["entity_id"] for m in items}
    assert all(r["payload"]["title"] == "Soup" and not r["deleted"] for r in all_rows)
    assert all(r["revision"] <= checkpoint["cursor"] for r in all_rows)
    assert first["checkpoint"] == second["checkpoint"] == checkpoint


def test_snapshot_includes_latest_tombstones_and_no_secret_tables(harness, mutation):
    c, _, device, tokens = harness
    item = mutation(device)
    assert push(c, item).status_code == 200
    assert (
        push(c, mutation(device, entity_id=item["entity_id"], operation="delete")).status_code
        == 200
    )
    data = c.get("/api/v1/sync/snapshot", params=anchor(c))
    rows = data.json()["changes"]
    assert len(rows) == 1 and rows[0]["deleted"] and rows[0]["revision"] == 2
    assert tokens["access_token"] not in data.text and "password_hash" not in data.text


def test_history_endpoints_validate_authentication_and_bounds(harness):
    c, _, _, _ = harness
    checkpoint = anchor(c)
    for changes in [
        {"limit": 101},
        {"after": "recipe:../../bad"},
        {"after": "session:" + str(uuid4())},
        {"token": "wrong"},
        {"cursor": -1},
    ]:
        assert c.get("/api/v1/sync/snapshot", params={**checkpoint, **changes}).status_code == 422
    assert c.get("/api/v1/sync/state?cursor=-1").status_code == 422
    c.headers.pop("Authorization")
    assert c.get("/api/v1/sync/state").status_code == 401
    assert c.get("/api/v1/sync/snapshot", params=checkpoint).status_code == 401


def test_legacy_history_migration_adds_once_only_proofs(harness, mutation):
    c, app, device, _ = harness
    assert push(c, mutation(device)).status_code == 200
    with app.state.database.connect() as db:
        db.execute("DROP INDEX change_commit_token")
        db.execute("ALTER TABLE change_log DROP COLUMN commit_token")
        db.execute("DELETE FROM schema_migration WHERE version='005_sync_history.sql'")
    Database(app.state.database.root)
    proof = anchor(c)
    assert len(proof["token"]) == 32
    Database(app.state.database.root)
    assert anchor(c) == proof


def test_append_does_not_invalidate_existing_anchor(harness, mutation):
    c, _, device, _ = harness
    assert push(c, mutation(device)).status_code == 200
    checkpoint = anchor(c)
    for _ in range(3):
        assert push(c, mutation(device), checkpoint=checkpoint).status_code == 200
    assert c.get("/api/v1/sync/snapshot", params=checkpoint).status_code == 200


def test_proof_guard_also_protects_delta_reads_after_a_restore(harness, mutation, tmp_path):
    c, app, device, _ = harness
    snapshot = tmp_path / "before.sqlite"
    backup(app.state.database, snapshot)
    assert push(c, mutation(device)).status_code == 200
    old = anchor(c)
    receipt = push(c, mutation(device)).json()[0]
    assert receipt["revision_token"] == anchor(c)["token"]
    restore(app.state.database, snapshot)
    assert push(c, mutation(device)).status_code == 200
    response = c.get("/api/v1/sync/pull", params=old)
    assert (
        response.status_code == 409 and response.json()["error"]["code"] == "sync_history_changed"
    )


def test_snapshot_pages_also_respect_a_soft_payload_budget(harness, mutation):
    c, _, device, _ = harness
    for _ in range(10):
        assert (
            push(
                c,
                mutation(device, payload={"title": "Large but valid", "steps": ["a" * 5000] * 50}),
            ).status_code
            == 200
        )
    checkpoint = anchor(c)
    first = c.get("/api/v1/sync/snapshot", params=checkpoint).json()
    assert 0 < len(first["changes"]) < 10 and first["next_after"]
    second = c.get(
        "/api/v1/sync/snapshot", params={**checkpoint, "after": first["next_after"]}
    ).json()
    assert len(first["changes"]) + len(second["changes"]) == 10 and second["next_after"] is None


def test_canonical_history_fixture_matches_the_versioned_wire_models():
    import json
    from pathlib import Path

    from mealf.models import MutationResult, Pull, SyncSnapshot, SyncState

    fixture = json.loads(Path("contracts/fixtures/sync-history-v1.json").read_text())
    assert fixture["format_version"] == 1
    for field, model in [
        ("state", SyncState),
        ("snapshot", SyncSnapshot),
        ("delta", Pull),
        ("receipt", MutationResult),
    ]:
        assert model.model_validate(fixture[field]).model_dump(mode="json") == fixture[field]
