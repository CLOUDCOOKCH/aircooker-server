import os
import sqlite3
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path

from .legacy import migrate_database


class Database:
    def __init__(self, data_dir: Path):
        try:
            self.max_bytes = int(os.environ.get("DATABASE_MAX_BYTES", str(2 * 1024**3)))
        except ValueError as exc:
            raise ValueError("DATABASE_MAX_BYTES must be an integer") from exc
        if not 1024**2 <= self.max_bytes <= 64 * 1024**3:
            raise ValueError("DATABASE_MAX_BYTES must be between 1 MiB and 64 GiB")
        self.root = data_dir
        for name in ("database", "media", "jobs", "backups", "config"):
            (data_dir / name).mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = data_dir / "database" / "mealf.sqlite3"
        migrate_database(self.path.parent)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS schema_migration(version TEXT PRIMARY KEY)")
            for migration in sorted(
                files("mealf").joinpath("migrations").iterdir(), key=lambda p: p.name
            ):
                if migration.name.endswith(".sql"):
                    # Single application process; startup migrations still hold a write lock.
                    db.execute("BEGIN EXCLUSIVE")
                    try:
                        if not db.execute(
                            "SELECT 1 FROM schema_migration WHERE version=?", (migration.name,)
                        ).fetchone():
                            for sql in migration.read_text().split(";"):
                                if sql.strip():
                                    db.execute(sql)
                            if migration.name == "006_pantry_period.sql":
                                from .data_migrations import pantry_periods

                                pantry_periods(db)
                            if migration.name == "009_import_retention.sql":
                                from .import_receipts import backfill

                                backfill(db)
                            db.execute("INSERT INTO schema_migration VALUES (?)", (migration.name,))
                        db.commit()
                    except BaseException:
                        db.rollback()
                        raise

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA busy_timeout=10000")
            page_size = db.execute("PRAGMA page_size").fetchone()[0]
            # Every connection needs its own cap. SQLite never truncates an existing
            # database when configured below its current size; it prevents growth.
            db.execute(f"PRAGMA max_page_count={self.max_bytes // page_size}")
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
