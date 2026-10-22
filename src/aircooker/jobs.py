import json
import time
from uuid import uuid4


# SQLite is the durable queue. Generation changes prevent a running reconciliation
# from swallowing changes that arrive while it calls the remote service.
def enqueue(db, kind: str, dedupe_key: str, payload: dict):
    now = time.time()
    db.execute(
        """INSERT INTO background_job
        (id,kind,dedupe_key,payload,state,available_at,created_at)
        VALUES (?,?,?,?,'queued',?,?) ON CONFLICT(dedupe_key) DO UPDATE SET
        payload=excluded.payload, generation=background_job.generation+1,
        state=CASE WHEN background_job.state='running' THEN 'running' ELSE 'queued' END,
        available_at=excluded.available_at, attempts=0, error_code=NULL""",
        (str(uuid4()), kind, dedupe_key, json.dumps(payload), now, now),
    )


def claim(database, lease_seconds=60):
    now = time.time()
    with database.transaction() as db:
        row = db.execute(
            """SELECT * FROM background_job WHERE
            (state='queued' AND available_at<=?) OR (state='running' AND lease_until<?)
            ORDER BY available_at LIMIT 1""",
            (now, now),
        ).fetchone()
        if not row:
            return None
        token = str(uuid4())
        db.execute(
            "UPDATE background_job SET state='running',lease_until=?,lease_token=?,claimed_generation=generation,attempts=attempts+1 WHERE id=?",
            (now + lease_seconds, token, row["id"]),
        )
        return dict(db.execute("SELECT * FROM background_job WHERE id=?", (row["id"],)).fetchone())


def finish(
    database, job, error_code=None, *, retry_after: int | None = None, terminal: bool = False
):
    with database.transaction() as db:
        current = db.execute(
            "SELECT * FROM background_job WHERE id=? AND lease_token=? AND state='running'",
            (job["id"], job["lease_token"]),
        ).fetchone()
        if not current:
            return False
        newer = current["generation"] != current["claimed_generation"]
        state = (
            "queued"
            if newer
            else (
                "done"
                if error_code is None
                else ("failed" if terminal or current["attempts"] >= 8 else "queued")
            )
        )
        delay = 0 if newer or error_code is None else min(3600, 2 ** current["attempts"])
        if not newer and error_code is not None and retry_after is not None:
            delay = max(delay, min(3600, max(0, retry_after)))
        db.execute(
            "UPDATE background_job SET state=?,available_at=?,lease_until=NULL,lease_token=NULL,error_code=? WHERE id=?",
            (state, time.time() + delay, error_code, job["id"]),
        )
        return True
