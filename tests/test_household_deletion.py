"""Synthetic local-operator deletion, process exclusion and fail-closed crash recovery."""

import asyncio
import json
import os
import subprocess
import sys
import threading
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from aircooker.app import create_app
from aircooker.deletion import MARKER, deletion_identity, erase_household
from aircooker.instance_lock import InstanceLock


def test_running_server_or_maintenance_cannot_share_the_data_volume(tmp_path):
    app = create_app(tmp_path)
    with TestClient(app):
        with pytest.raises(RuntimeError, match="Stop the server"):
            InstanceLock(tmp_path)
        with pytest.raises(RuntimeError, match="Stop the server"):
            create_app(tmp_path)
    with InstanceLock(tmp_path):
        pass


def test_shutdown_retains_volume_lock_until_worker_thread_stops(tmp_path, monkeypatch):
    import aircooker.app as application

    entered, release = threading.Event(), threading.Event()

    def slow_claim(database):
        entered.set()
        assert release.wait(timeout=5)
        return None

    monkeypatch.setattr(application, "claim", slow_claim)
    monkeypatch.setenv("LOG_SETUP_TOKEN", "false")
    app = create_app(tmp_path)

    async def check():
        manager = app.router.lifespan_context(app)
        await manager.__aenter__()
        try:
            async with asyncio.timeout(3):
                while not entered.is_set():
                    await asyncio.sleep(0.01)
            shutdown = asyncio.create_task(manager.__aexit__(None, None, None))
            await asyncio.sleep(0.05)
            assert not shutdown.done()
            with pytest.raises(RuntimeError, match="Stop the server"):
                InstanceLock(tmp_path)
            release.set()
            await asyncio.wait_for(shutdown, 3)
            with InstanceLock(tmp_path):
                pass
        finally:
            release.set()

    asyncio.run(check())


@pytest.mark.parametrize("include_backups", [False, True])
def test_explicit_offline_erasure_removes_current_secrets_and_rotates_identity(
    harness, include_backups
):
    client, app, _, _ = harness
    root = app.state.database.root
    old_identity = client.get("/api/v1/system/info").json()["instance_id"]
    (root / "config/synthetic-credential.enc").write_bytes(b"synthetic credential")
    backup = root / "backups/synthetic.sqlite3"
    backup.write_bytes(b"synthetic private backup")
    with InstanceLock(root):
        erase_household(root, old_identity, include_backups=include_backups)
    assert backup.exists() is not include_backups
    assert not (root / "config").exists() and not (root / "database").exists()
    assert not (root / MARKER).exists()
    fresh = create_app(root, run_worker=False)
    with TestClient(fresh) as new_client:
        assert new_client.get("/api/v1/system/info").json()["configured"] is False
        response = new_client.post(
            "/api/v1/setup",
            headers={"X-Setup-Token": (root / "config/setup-token").read_text()},
            json={
                "name": "New synthetic household",
                "username": "newcook",
                "password": "new synthetic password",
                "device_id": str(uuid4()),
            },
        )
        assert response.status_code == 201
        assert new_client.get("/api/v1/system/info").json()["instance_id"] != old_identity
        assert new_client.get("/api/v1/recipes", headers=dict(client.headers)).status_code == 401


def test_wrong_identity_cannot_start_deletion(harness):
    _, app, _, _ = harness
    root = app.state.database.root
    with InstanceLock(root), pytest.raises(ValueError, match="identity changed"):
        erase_household(root, str(uuid4()))
    assert not (root / MARKER).exists()
    assert (root / "database/aircooker.sqlite3").exists()


def test_interrupted_erasure_blocks_server_and_can_resume_same_intent(harness, monkeypatch):
    client, app, _, _ = harness
    root = app.state.database.root
    instance = client.get("/api/v1/system/info").json()["instance_id"]
    import aircooker.deletion as deletion

    original = deletion.shutil.rmtree
    calls = []

    def interrupted(path):
        calls.append(path.name)
        if len(calls) == 2:
            raise OSError("synthetic deletion interruption")
        return original(path)

    with InstanceLock(root), monkeypatch.context() as patch:
        patch.setattr(deletion.shutil, "rmtree", interrupted)
        with pytest.raises(OSError):
            erase_household(root, instance, include_backups=True)
    assert (root / MARKER).exists() and not (root / "database").exists()
    with pytest.raises(RuntimeError, match="deletion is incomplete"):
        create_app(root)
    assert deletion_identity(root) == (instance, True)
    with InstanceLock(root):
        with pytest.raises(ValueError, match="original backup-deletion choice"):
            erase_household(root, instance)
        erase_household(root, instance, include_backups=True)
    assert not (root / MARKER).exists()


def test_symlinked_data_is_never_followed_and_marker_is_private(harness, tmp_path):
    client, app, _, _ = harness
    root = app.state.database.root
    outside = tmp_path / "outside"
    outside.mkdir()
    private = outside / "keep.txt"
    private.write_text("synthetic unrelated file")
    (root / "media").rmdir()
    (root / "media").symlink_to(outside, target_is_directory=True)
    with InstanceLock(root), pytest.raises(ValueError, match="symlinks"):
        erase_household(root, client.get("/api/v1/system/info").json()["instance_id"])
    assert private.read_text() == "synthetic unrelated file"
    assert (root / MARKER).stat().st_mode & 0o777 == 0o600


def test_noninteractive_cli_refuses_deletion_before_touching_data(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "aircooker.cli", "delete-household"],
        input="DELETE synthetic\n",
        text=True,
        capture_output=True,
        env={**os.environ, "DATA_DIR": str(tmp_path / "untouched")},
    )
    assert result.returncode != 0 and "interactive local terminal" in result.stderr
    assert not (tmp_path / "untouched").exists()


def test_actual_cli_requires_exact_terminal_confirmation(harness, monkeypatch):
    from pathlib import Path

    monkeypatch.syspath_prepend(str(Path(__file__).parents[1] / "scripts"))
    from operator_docker_smoke import PTY_RUNNER

    client, app, _, _ = harness
    root = app.state.database.root
    instance = client.get("/api/v1/system/info").json()["instance_id"]
    for confirmation, expected in [("DELETE wrong", False), ("DELETE " + instance, True)]:
        run = subprocess.run(
            [sys.executable, "-c", PTY_RUNNER, confirmation, "[]"],
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, "DATA_DIR": str(root)},
        )
        assert run.returncode == 0, run.stderr
        result = json.loads(run.stdout)
        assert (result["code"] == 0) is expected, result
        assert (root / "database/aircooker.sqlite3").exists() is not expected


def test_malformed_deletion_marker_cannot_silently_create_a_household(tmp_path):
    (tmp_path / MARKER).write_text(json.dumps({"format": "unexpected"}))
    with pytest.raises(RuntimeError, match="deletion is incomplete"):
        create_app(tmp_path)
    assert not (tmp_path / "database").exists()
