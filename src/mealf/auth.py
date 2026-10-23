import hashlib
import secrets
import time
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from .errors import DomainError
from .models import Tokens

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(32))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def rate_limit(db, key: str, maximum: int = 10, seconds: int = 300):
    now = time.time()
    db.execute("DELETE FROM rate_limit WHERE resets < ?", (now,))
    db.execute(
        "INSERT INTO rate_limit VALUES (?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1",
        (key, now + seconds),
    )
    return db.execute("SELECT count FROM rate_limit WHERE key=?", (key,)).fetchone()[0] <= maximum


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return hasher.verify(password_hash, password)
    except VerificationError:
        return False


def new_session(db, device_id: str, session_id: str | None = None, *, user_id: str) -> Tokens:
    now = time.time()
    db.execute(
        "INSERT INTO device VALUES (?,?) ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen",
        (device_id, now),
    )
    sid = session_id or str(uuid4())
    access, refresh = secrets.token_urlsafe(48), secrets.token_urlsafe(48)
    if session_id:
        db.execute(
            "UPDATE session SET access_hash=?,refresh_hash=?,access_expires=?,refresh_expires=? WHERE id=?",
            (digest(access), digest(refresh), now + 900, now + 30 * 86400, sid),
        )
    else:
        db.execute(
            "INSERT INTO session(id,device_id,access_hash,refresh_hash,access_expires,refresh_expires,revoked,user_id) VALUES (?,?,?,?,?,?,0,?)",
            (sid, device_id, digest(access), digest(refresh), now + 900, now + 30 * 86400, user_id),
        )
    return Tokens(access_token=access, refresh_token=refresh, session_id=UUID(sid))


def authenticate(db, token: str):
    row = db.execute(
        "SELECT s.*,u.role,u.username FROM session s JOIN household_user u ON u.id=s.user_id "
        "WHERE access_hash=? AND revoked=0 AND access_expires>? AND refresh_expires>? AND u.active=1",
        (digest(token), time.time(), time.time()),
    ).fetchone()
    if not row:
        raise DomainError("authentication_required", 401)
    return dict(row)


def refresh_session(database, token: str):
    # Revocation on replay must commit even though the response is an error.
    result = None
    with database.transaction() as db:
        row = db.execute(
            "SELECT s.* FROM session s JOIN household_user u ON u.id=s.user_id "
            "WHERE refresh_hash=? AND revoked=0 AND refresh_expires>? AND u.active=1",
            (digest(token), time.time()),
        ).fetchone()
        if row:
            db.execute("INSERT INTO refresh_history VALUES (?,?)", (digest(token), row["id"]))
            result = new_session(db, row["device_id"], row["id"], user_id=row["user_id"])
        else:
            previous = db.execute(
                "SELECT session_id FROM refresh_history WHERE token_hash=?", (digest(token),)
            ).fetchone()
            if previous:
                db.execute("UPDATE session SET revoked=1 WHERE id=?", (previous[0],))
    if result is None:
        raise DomainError("invalid_refresh_token", 401)
    return result


def revoke_refresh_capability(database, token: str):
    """A refresh secret can only revoke its own session, including after rotation.

    Return no account/session information, even for unknown or expired capabilities.
    Retained refresh history already permits revocation on refresh-token replay.
    """
    token_hash = digest(token)
    with database.transaction() as db:
        db.execute(
            "UPDATE session SET revoked=1 WHERE refresh_hash=? OR id IN "
            "(SELECT session_id FROM refresh_history WHERE token_hash=?)",
            (token_hash, token_hash),
        )
