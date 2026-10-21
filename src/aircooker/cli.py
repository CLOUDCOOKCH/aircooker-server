import argparse
import getpass
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

from .auth import hasher
from .db import Database
from .retention import cleanup_database


def main():
    parser = argparse.ArgumentParser(
        description="Local administrator tools; requires access to /data"
    )
    parser.add_argument("command", choices=["recover", "backup", "cleanup"])
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--dry-run", action="store_true", help="Report cleanup candidates without pruning rows"
    )
    args = parser.parse_args()
    if args.dry_run and args.command != "cleanup":
        parser.error("--dry-run only applies to cleanup")
    os.umask(0o077)
    database = Database(Path(os.environ.get("DATA_DIR", "/data")))
    if args.command == "cleanup":
        print(
            json.dumps(
                {
                    "dry_run": args.dry_run,
                    "counts": cleanup_database(database, dry_run=args.dry_run),
                }
            )
        )
    elif args.command == "recover":
        if not sys.stdin.isatty():
            parser.error("Recovery requires an interactive local terminal")
        password = getpass.getpass("New household password (at least 12 characters): ")
        if len(password) < 12 or password != getpass.getpass("Repeat password: "):
            parser.error("Passwords do not match or are too short")
        with database.transaction() as db:
            if not db.execute("SELECT 1 FROM household").fetchone():
                parser.error("Complete first-run setup before recovery")
            db.execute("UPDATE household SET password_hash=?", (hasher.hash(password),))
            db.execute("UPDATE session SET revoked=1")
            db.execute(
                "INSERT INTO audit_event(code,created_at) VALUES (?,?)",
                ("local_password_recovery", time.time()),
            )
        print("Password changed. All device and browser sessions revoked.")
    elif args.command == "backup":
        if not args.output or args.output.exists():
            parser.error("--output must be a new local path; backup contains secrets")
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(fd)
        with database.connect() as source, sqlite3.connect(args.output) as target:
            source.backup(target)
        print(
            "Sensitive SQLite backup created; encrypt before moving off-host. Media must be backed up separately."
        )


if __name__ == "__main__":
    main()
