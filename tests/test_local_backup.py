import sqlite3
from contextlib import contextmanager

import pytest

from mealf.local_backup import create_backup


def test_verified_snapshot_has_private_permissions_and_preserves_wal_data(harness):
    _, app, _, _ = harness
    database = app.state.database
    target = database.root / "backups/verified.sqlite3"
    with database.transaction() as db:
        db.execute("CREATE TABLE synthetic_backup_probe(content TEXT)")
        db.execute("INSERT INTO synthetic_backup_probe VALUES ('retained WAL content')")
    create_backup(database, target)
    assert target.stat().st_mode & 0o777 == 0o600
    with sqlite3.connect(target) as restored:
        assert restored.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        assert (
            restored.execute("SELECT content FROM synthetic_backup_probe").fetchone()[0]
            == "retained WAL content"
        )
        assert restored.execute("SELECT instance_id FROM household").fetchone()[0]
    assert list(target.parent.glob(".backup-*")) == []
    with pytest.raises(FileExistsError):
        create_backup(database, target)


def test_failed_copy_never_publishes_a_partial_backup(harness, monkeypatch):
    _, app, _, _ = harness
    database = app.state.database
    target = database.root / "backups/not-published.sqlite3"

    @contextmanager
    def broken():
        raise sqlite3.OperationalError("synthetic interrupted copy")
        yield

    monkeypatch.setattr(database, "connect", broken)
    with pytest.raises(sqlite3.OperationalError):
        create_backup(database, target)
    assert not target.exists() and list(target.parent.glob(".backup-*")) == []


def test_destination_race_never_overwrites_another_operators_backup(harness, monkeypatch):
    import mealf.local_backup as backup

    _, app, _, _ = harness
    target = app.state.database.root / "backups/raced.sqlite3"
    original = backup.os.link

    def raced(source, destination):
        target.write_bytes(b"another operator's synthetic backup")
        original(source, destination)

    monkeypatch.setattr(backup.os, "link", raced)
    with pytest.raises(FileExistsError):
        create_backup(app.state.database, target)
    assert target.read_bytes() == b"another operator's synthetic backup"
    assert list(target.parent.glob(".backup-*")) == []
