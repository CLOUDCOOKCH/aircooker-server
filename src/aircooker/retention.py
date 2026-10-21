"""Bounded maintenance preserves pending work, replay identities and offline sync history."""

import os
import stat
import time
from pathlib import Path

DAY = 86400
BATCH = 500


def cleanup_database(database, *, now=None, dry_run=False):
    now = time.time() if now is None else now
    counts = {}
    with database.transaction() as db:
        # A draft's minimal request receipt and final state remain available indefinitely.
        imports = db.execute(
            """SELECT id FROM import_draft WHERE state IN ('confirmed','cancelled')
            AND finished_at<? AND request_fingerprint IS NOT NULL
            AND (recipe IS NOT NULL OR warnings!='[]' OR error_code IS NOT NULL)
            LIMIT ?""",
            (now - 30 * DAY, BATCH),
        ).fetchall()
        counts["import_previews"] = len(imports)
        for row in imports:
            if not dry_run:
                db.execute(
                    "UPDATE import_draft SET recipe=NULL,warnings='[]',error_code=NULL WHERE id=?",
                    (row["id"],),
                )
        jobs = db.execute(
            """SELECT j.id FROM background_job j WHERE j.state IN ('done','failed') AND (
                (j.kind='recipe.import' AND EXISTS (SELECT 1 FROM import_draft i
                    WHERE j.dedupe_key='import:'||i.id AND i.state IN ('confirmed','cancelled')
                    AND i.finished_at<? AND i.request_fingerprint IS NOT NULL))
                OR (j.state='done' AND j.available_at<? AND j.kind IN ('notification.meal','notification.test')
                    AND (NOT EXISTS (SELECT 1 FROM push_subscription p
                            WHERE j.dedupe_key LIKE 'push.%:'||p.id||':%')
                        OR EXISTS (SELECT 1 FROM push_delivery d
                            WHERE j.dedupe_key='push.meal:'||d.subscription_id||':'||d.planned_date||':'||d.category)))
            ) LIMIT ?""",
            (now - 30 * DAY, now - 30 * DAY, BATCH),
        ).fetchall()
        counts["terminal_jobs"] = len(jobs)
        for row in jobs:
            if not dry_run:
                db.execute("DELETE FROM background_job WHERE id=?", (row["id"],))
        sessions = db.execute(
            """SELECT s.id FROM session s WHERE s.refresh_expires<?
            AND NOT EXISTS (SELECT 1 FROM push_subscription p WHERE p.session_id=s.id) LIMIT ?""",
            (now - 90 * DAY, BATCH),
        ).fetchall()
        counts["expired_sessions"] = len(sessions)
        for row in sessions:
            if not dry_run:
                db.execute("DELETE FROM refresh_history WHERE session_id=?", (row["id"],))
                db.execute("DELETE FROM session WHERE id=?", (row["id"],))
        for table, column, cutoff in (
            ("audit_event", "created_at", now - 90 * DAY),
            ("rate_limit", "resets", now - DAY),
        ):
            # Identifiers are fixed application constants, never user input.
            ids = db.execute(
                f"SELECT rowid FROM {table} WHERE {column}<? LIMIT ?", (cutoff, BATCH)
            ).fetchall()
            counts[table] = len(ids)
            if not dry_run:
                db.executemany(f"DELETE FROM {table} WHERE rowid=?", [(row[0],) for row in ids])
    return counts


def cleanup_startup_transfers(root: Path, *, now=None):
    """Run before serving requests in the supported single-process deployment, never mid-transfer."""
    now = time.time() if now is None else now
    count = 0
    with os.scandir(root / "jobs") as entries:
        for entry in entries:
            if count >= BATCH:
                break
            if not (
                entry.name.startswith((".export-", ".restore-")) and entry.name.endswith(".zip")
            ):
                continue
            try:
                metadata = entry.stat(follow_symlinks=False)
                if stat.S_ISREG(metadata.st_mode) and metadata.st_mtime < now - DAY:
                    os.unlink(entry.path)
                    count += 1
            except FileNotFoundError:
                continue
    return count
