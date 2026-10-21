import sqlite3
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path


class Database:
    def __init__(self, data_dir: Path):
        self.root = data_dir
        for name in ("database", "media", "jobs", "backups", "config"):
            (data_dir / name).mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = data_dir / "database" / "aircooker.sqlite3"
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS schema_migration(version TEXT PRIMARY KEY)")
            for migration in sorted(
                files("aircooker").joinpath("migrations").iterdir(), key=lambda p: p.name
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
                            db.execute("INSERT INTO schema_migration VALUES (?)", (migration.name,))
                        db.commit()
                    except BaseException:
                        db.rollback()
                        raise

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA busy_timeout=10000")
        try:
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
