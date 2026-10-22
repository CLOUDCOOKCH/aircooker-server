"""Immutable commit proofs and bounded snapshots anchored to retained history.

No history compaction is enabled. A snapshot reads the latest change of each identity at
or before its anchor, so concurrent later writes cannot change earlier pages.
"""

import json
from sqlite3 import Row
from uuid import UUID

from .errors import DomainError
from .models import Change, SyncAnchor, SyncSnapshot, SyncState
from .sync import token_at


def validate_anchor(db, anchor: SyncAnchor):
    if token_at(db, anchor.cursor) != anchor.token:
        raise DomainError("sync_history_changed", 409)


def state_for(db, cursor: int):
    # One statement fixes head, requested proof and identity to the same SQLite snapshot.
    row = db.execute(
        """SELECT instance_id,
        COALESCE((SELECT MAX(sequence) FROM change_log),0) AS high,
        (SELECT commit_token FROM change_log ORDER BY sequence DESC LIMIT 1) AS head_token,
        (SELECT commit_token FROM change_log WHERE sequence=?) AS requested_token
        FROM household WHERE id=1""",
        (cursor,),
    ).fetchone()
    return SyncState(
        instance_id=row["instance_id"],
        cursor=row["high"],
        token=row["head_token"] or "root",
        requested_cursor=cursor,
        requested_token="root" if cursor == 0 else row["requested_token"],
    )


def snapshot_page(db, anchor: SyncAnchor, after: str, limit: int):
    # Keep anchor validation, household identity and rows in one read transaction.
    db.execute("BEGIN")
    validate_anchor(db, anchor)
    if after:
        try:
            kind, identity = after.split(":", 1)
            if kind not in {"recipe", "meal", "pantry", "leftover", "template"}:
                raise ValueError()
            if str(UUID(identity)) != identity:
                raise ValueError()
        except (ValueError, AttributeError) as exc:
            raise DomainError("invalid_snapshot_cursor", 422) from exc
    else:
        kind, identity = "", ""
    rows = db.execute(
        """WITH latest AS (
              SELECT kind,entity_id,MAX(sequence) AS seq FROM change_log
              WHERE sequence<=? GROUP BY kind,entity_id
            ) SELECT c.* FROM latest l JOIN change_log c ON c.sequence=l.seq
              WHERE (c.kind,c.entity_id)>(?,?) ORDER BY c.kind,c.entity_id LIMIT ?""",
        (anchor.cursor, kind, identity, limit + 1),
    )
    selected: list[Row] = []
    used = 0
    has_more = False
    for row in rows:
        size = len(row["payload"].encode("utf-8")) + 512
        if selected and (len(selected) >= limit or used + size > 2 * 1024 * 1024):
            has_more = True
            break
        selected.append(row)
        used += size

    return SyncSnapshot(
        instance_id=db.execute("SELECT instance_id FROM household WHERE id=1").fetchone()[0],
        checkpoint=anchor,
        changes=[
            Change(
                revision=r["sequence"],
                kind=r["kind"],
                entity_id=r["entity_id"],
                deleted=bool(r["deleted"]),
                payload=json.loads(r["payload"]),
                updated_at=r["updated_at"],
            )
            for r in selected
        ],
        next_after=(f"{selected[-1]['kind']}:{selected[-1]['entity_id']}" if has_more else None),
    )
