"""Publish only a verified, consistent sensitive SQLite backup; never overwrite one."""

import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


def create_backup(database, output: Path):
    if output.exists() or output.is_symlink():
        raise FileExistsError("Backup destination already exists")
    fd, temporary = tempfile.mkstemp(prefix=".backup-", suffix=".sqlite3", dir=output.parent)
    os.close(fd)
    staged = Path(temporary)
    try:
        with database.connect() as source, closing(sqlite3.connect(staged)) as target:
            source.backup(target)
            if (
                target.execute("PRAGMA quick_check").fetchone()[0] != "ok"
                or target.execute("PRAGMA foreign_key_check").fetchone()
            ):
                raise ValueError("Backup integrity validation failed")
        with staged.open("rb") as copied:
            os.fsync(copied.fileno())
        # Same-directory link publication is atomic and refuses a destination
        # another operator created during copying. No partial file is called ready.
        os.link(staged, output)
        directory = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        staged.unlink(missing_ok=True)
