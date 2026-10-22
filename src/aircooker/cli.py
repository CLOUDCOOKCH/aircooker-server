import argparse
import getpass
import json
import os
import sys
import time
from pathlib import Path

from .auth import hasher
from .db import Database
from .deletion import deletion_identity, erase_household
from .instance_lock import InstanceLock
from .local_backup import create_backup
from .retention import cleanup_database


def main():
    parser = argparse.ArgumentParser(
        description="Local administrator tools; requires access to /data"
    )
    parser.add_argument("command", choices=["recover", "backup", "cleanup", "delete-household"])
    parser.add_argument(
        "--include-backups",
        action="store_true",
        help="Also erase application-managed backups during explicit household deletion",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--dry-run", action="store_true", help="Report cleanup candidates without pruning rows"
    )
    args = parser.parse_args()
    if args.dry_run and args.command != "cleanup":
        parser.error("--dry-run only applies to cleanup")
    if args.include_backups and args.command != "delete-household":
        parser.error("--include-backups only applies to delete-household")
    os.umask(0o077)
    root = Path(os.environ.get("DATA_DIR", "/data"))
    if args.command == "delete-household":
        if not sys.stdin.isatty():
            parser.error("Household deletion requires an interactive local terminal")
        try:
            with InstanceLock(root):
                instance, _ = deletion_identity(root)
                print(
                    "This permanently erases this household, sessions, recipes, jobs and saved integration credentials."
                )
                print(
                    "Application backups will also be erased."
                    if args.include_backups
                    else "Application backups are retained and can still contain private data."
                )
                print(
                    "Offline device copies, external secrets, external services and off-host backups are unaffected."
                )
                if input(f"Type DELETE {instance} to continue: ") != f"DELETE {instance}":
                    parser.error("Confirmation did not match; nothing was deleted")
                erase_household(root, instance, include_backups=args.include_backups)
        except (RuntimeError, ValueError, OSError) as exc:
            parser.error(str(exc))
        print("Household erased. Restart for fresh setup with a new household identity.")
        return
    database = Database(root)
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
        create_backup(database, args.output)
        print(
            "Sensitive SQLite backup created (including stored recipe photo BLOBs); encrypt before moving off-host. Configuration/encryption keys must be backed up separately."
        )


if __name__ == "__main__":
    main()
