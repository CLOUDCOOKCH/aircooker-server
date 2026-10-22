"""Explicit offline household erasure; interrupted operations block normal startup."""

import json
import os
import shutil
from pathlib import Path
from uuid import UUID

from .db import Database

MARKER = ".household-deletion.json"


def sync_root(root):
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def deletion_identity(root: Path):
    marker = root / MARKER
    if marker.is_symlink():
        raise ValueError("Deletion marker must not be a symlink")
    if marker.exists():
        data = json.loads(marker.read_text())
        if data.get("format") != "mealf-household-deletion" or not isinstance(
            data.get("include_backups"), bool
        ):
            raise ValueError("Invalid deletion marker; recover the volume before starting")
        return str(UUID(data["instance_id"])), data["include_backups"]
    if not (root / "database/aircooker.sqlite3").is_file():
        raise ValueError("No configured household at DATA_DIR")
    with Database(root).connect() as db:
        household = db.execute("SELECT instance_id FROM household WHERE id=1").fetchone()
    if not household:
        raise ValueError("No configured household at DATA_DIR")
    return str(UUID(household[0])), None


def erase_household(root: Path, instance_id: str, *, include_backups=False):
    """Caller holds InstanceLock and has obtained explicit interactive confirmation."""
    expected, resumed_backups = deletion_identity(root)
    if str(UUID(instance_id)) != expected:
        raise ValueError("Household identity changed; nothing was deleted")
    if resumed_backups is not None and resumed_backups != include_backups:
        raise ValueError("Resume using the original backup-deletion choice")
    marker = root / MARKER
    if not marker.exists():
        data = json.dumps(
            {
                "format": "mealf-household-deletion",
                "instance_id": expected,
                "include_backups": include_backups,
            }
        )
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        sync_root(root)
    # The lock/marker live outside these directories. A restart cannot bypass an
    # interrupted erasure by creating a fresh lock inode or a partial new household.
    names = ["database", "media", "jobs", "config"] + (["backups"] if include_backups else [])
    for name in names:
        path = root / name
        if path.is_symlink():
            raise ValueError("Application data directories must not be symlinks")
        if path.exists():
            shutil.rmtree(path)
    sync_root(root)
    marker.unlink()
    sync_root(root)
