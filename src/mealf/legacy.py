"""Read-only compatibility identifiers from previews published before the full rename.

New writes/exports use Mealf names. Do not remove these while older clients, saved
volumes and portable archives can still contain them.
"""

import os
import sqlite3

PREFIX = "aircooker"
DATABASE_NAME = PREFIX + ".sqlite3"
HEADER_PREFIX = "x-" + PREFIX
EXPORT_FORMAT = PREFIX + "-household"
ARCHIVE_FORMAT = PREFIX + "-household-archive"


def cookie(request, name):
    if name in request.cookies:
        return request.cookies[name]
    return request.cookies.get(name.replace("mealf", PREFIX, 1), "")


def migrate_database(directory):
    """Caller holds the existing data-volume lease; checkpoint before changing names."""
    old, current = directory / DATABASE_NAME, directory / "mealf.sqlite3"
    if not old.exists():
        return
    if old.is_symlink() or current.is_symlink():
        raise RuntimeError("Database paths must not be symbolic links")
    if current.exists():
        if not os.path.samefile(old, current):
            raise RuntimeError(
                "Two different household databases exist; recover the correct volume before starting"
            )
        # Resume a crash between link publication and removal of the old name.
        old.unlink()
    else:
        connection = sqlite3.connect(old, timeout=10, isolation_level=None)
        try:
            result = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            if result[0]:
                raise RuntimeError("Stop every database reader/writer before upgrading this volume")
        finally:
            connection.close()
        wal = directory / (DATABASE_NAME + "-wal")
        if wal.exists() and wal.stat().st_size:
            raise RuntimeError("Database WAL is still active; stop every database reader/writer")
        # Never replace a database another process/operator created.
        os.link(old, current)
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        old.unlink()
    for suffix in ("-wal", "-shm"):
        path = directory / (DATABASE_NAME + suffix)
        path.unlink(missing_ok=True)
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
