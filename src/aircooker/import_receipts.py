"""Stable request receipts let terminal imports shed source text without losing replay safety."""

import hashlib
import json
import time

FIELDS = ("text", "source_url", "use_ai", "consent_external_ai")


def fingerprint(values):
    identity = {key: values[key] for key in FIELDS}
    # Preserve every pre-image receipt byte-for-byte for offline replay.
    if values.get("image_id") is not None:
        identity["image_id"] = str(values["image_id"])
    return hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def backfill(db):
    now = time.time()
    after = ""
    while True:
        rows = db.execute(
            """SELECT i.id,j.payload FROM import_draft i JOIN background_job j
            ON j.dedupe_key='import:'||i.id WHERE i.request_fingerprint IS NULL AND i.id>?
            ORDER BY i.id LIMIT 100""",
            (after,),
        ).fetchall()
        if not rows:
            break
        for row in rows:
            after = row["id"]
            try:
                values = json.loads(row["payload"])
                if not isinstance(values, dict) or any(key not in values for key in FIELDS):
                    continue
                if any(
                    values[key] is not None and not isinstance(values[key], str)
                    for key in ("text", "source_url")
                ):
                    continue
                if any(
                    not isinstance(values[key], bool) for key in ("use_ai", "consent_external_ai")
                ):
                    continue
                receipt = fingerprint(values)
            except (ValueError, TypeError):
                # Unknown legacy data stays retained; do not guess a replay identity.
                continue
            db.execute(
                "UPDATE import_draft SET request_fingerprint=? WHERE id=?", (receipt, row["id"])
            )
    # Historical completion time is unknown: give every existing terminal draft a fresh grace period.
    db.execute(
        "UPDATE import_draft SET finished_at=? WHERE state IN ('confirmed','cancelled')", (now,)
    )
