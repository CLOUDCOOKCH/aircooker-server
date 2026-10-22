"""Device-scoped, opt-in meal reminders, with durable accepted-delivery receipts."""

import hashlib
import json
import os
import time
from datetime import UTC, date, datetime
from datetime import time as civil_time
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from cryptography.hazmat.primitives.asymmetric import ec
from pydantic import Field, field_validator

from .errors import DomainError
from .jobs import enqueue
from .models import Meal, Model
from .planning import entities, occurrences
from .secrets import SecretVault
from .webpush import WebPushTransport, encoded, endpoint_origin, key_bytes

CATEGORIES = ("breakfast", "lunch", "dinner")
GRACE = 15 * 60


class PushDeliveryError(DomainError):
    def __init__(self, code, retry_after=None):
        super().__init__(code, 503)
        self.retry_after = retry_after


class ReminderPreferences(Model):
    enabled: bool = True
    breakfast: str | None = "07:30"
    lunch: str | None = "12:00"
    dinner: str | None = "18:00"

    @field_validator("breakfast", "lunch", "dinner")
    @classmethod
    def valid_time(cls, value):
        if value is not None:
            parsed = civil_time.fromisoformat(value)
            if parsed.isoformat(timespec="minutes") != value or parsed.tzinfo is not None:
                raise ValueError("Use HH:MM household time")
        return value


class PushKeys(Model):
    p256dh: str = Field(max_length=100)
    auth: str = Field(max_length=40)

    @field_validator("p256dh")
    @classmethod
    def valid_public(cls, value):
        raw = key_bytes(value, 65)
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), raw)
        return encoded(raw)

    @field_validator("auth")
    @classmethod
    def valid_auth(cls, value):
        return encoded(key_bytes(value, 16))


class PushRegistration(Model):
    endpoint: str = Field(max_length=4096)
    keys: PushKeys
    language: Literal["en", "de"] = "en"
    preferences: ReminderPreferences = Field(default_factory=ReminderPreferences)

    @field_validator("endpoint")
    @classmethod
    def valid_endpoint(cls, value):
        endpoint_origin(value)
        return value


class PushSettings(Model):
    language: Literal["en", "de"] = "en"
    preferences: ReminderPreferences


class PushStatus(Model):
    available: bool
    public_key: str
    subscribed: bool
    preferences: ReminderPreferences
    last_success: float | None = None
    error_code: str | None = None
    pending_jobs: int = 0
    failed_jobs: int = 0
    subscription_fingerprint: str | None = None


class PushTest(Model):
    request_id: UUID


class PushQueued(Model):
    state: Literal["queued"] = "queued"


class PushRetried(PushQueued):
    count: int


def due_at(day: date, clock: str, timezone: str):
    zone = ZoneInfo(timezone)
    local = datetime.combine(day, civil_time.fromisoformat(clock), zone)
    # First fold on autumn overlap; spring's nonexistent time shifts forward across the gap.
    return local.astimezone(UTC)


class Reminders:
    def __init__(self, database, config):
        self.database = database
        self.vault = SecretVault(config)
        self.subject = os.environ.get("BASE_URL", "https://localhost").rstrip("/")
        try:
            origin = urlsplit(self.subject)
            self.available = bool(
                origin.scheme == "https"
                and origin.hostname
                and origin.hostname != "localhost"
                and not origin.hostname.endswith(".localhost")
                and origin.username is None
                and origin.password is None
                and not origin.path
                and not origin.query
                and not origin.fragment
            )
        except ValueError:
            self.available = False
        self.transport = WebPushTransport(self.vault, self.subject)

    def status(self, device_id):
        with self.database.connect() as db:
            row = db.execute(
                """SELECT p.*,s.revoked,s.refresh_expires FROM push_subscription p
                JOIN session s ON s.id=p.session_id WHERE p.device_id=?""",
                (device_id,),
            ).fetchone()
            counts = {"pending": 0, "failed": 0}
            if row:
                for state in db.execute(
                    "SELECT state,COUNT(*) AS n FROM background_job WHERE (dedupe_key LIKE ? OR dedupe_key LIKE ?) GROUP BY state",
                    (f"push.meal:{row['id']}:%", f"push.test:{row['id']}:%"),
                ):
                    if state["state"] in ("queued", "running"):
                        counts["pending"] += state["n"]
                    elif state["state"] == "failed":
                        counts["failed"] += state["n"]
        session_expired = bool(row and (row["revoked"] or row["refresh_expires"] <= time.time()))
        subscribed = bool(row and row["enabled"] and not session_expired)
        return PushStatus(
            available=self.available,
            public_key=self.transport.public_key,
            subscribed=subscribed,
            preferences=ReminderPreferences.model_validate_json(row["preferences"])
            if row
            else ReminderPreferences(enabled=False),
            last_success=row["last_success"] if row else None,
            error_code="push_session_expired"
            if session_expired
            else row["error_code"]
            if row
            else None,
            pending_jobs=counts["pending"],
            failed_jobs=counts["failed"],
            subscription_fingerprint=row["endpoint_hash"] if subscribed else None,
        )

    def register(self, session, body: PushRegistration):
        if not self.available:
            raise DomainError("push_https_required", 409)
        endpoint_hash = hashlib.sha256(body.endpoint.encode()).hexdigest()
        credentials = self.vault.cipher.encrypt(
            json.dumps({"endpoint": body.endpoint, "keys": body.keys.model_dump()}).encode()
        ).decode()
        with self.database.transaction() as db:
            prior = db.execute(
                "SELECT device_id FROM push_subscription WHERE endpoint_hash=?", (endpoint_hash,)
            ).fetchone()
            if prior and prior["device_id"] != session["device_id"]:
                raise DomainError("push_endpoint_already_registered", 409)
            existing = db.execute(
                "SELECT id,enabled FROM push_subscription WHERE device_id=?",
                (session["device_id"],),
            ).fetchone()
            if (not existing or not existing["enabled"]) and db.execute(
                "SELECT COUNT(*) FROM push_subscription WHERE enabled=1"
            ).fetchone()[0] >= 50:
                raise DomainError("push_subscription_limit", 409)
            db.execute(
                """INSERT INTO push_subscription
                (id,device_id,session_id,endpoint_hash,credentials,preferences,language,updated_at)
                VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(device_id) DO UPDATE SET
                session_id=excluded.session_id,endpoint_hash=excluded.endpoint_hash,
                credentials=excluded.credentials,preferences=excluded.preferences,
                language=excluded.language,enabled=1,error_code=NULL,updated_at=excluded.updated_at""",
                (
                    str(uuid4()),
                    session["device_id"],
                    session["id"],
                    endpoint_hash,
                    credentials,
                    body.preferences.model_dump_json(),
                    body.language,
                    time.time(),
                ),
            )
        return self.status(session["device_id"])

    def set_preferences(self, session, body: PushSettings):
        with self.database.transaction() as db:
            changed = db.execute(
                """UPDATE push_subscription SET preferences=?,language=?,session_id=?,updated_at=?
                WHERE device_id=? AND enabled=1""",
                (
                    body.preferences.model_dump_json(),
                    body.language,
                    session["id"],
                    time.time(),
                    session["device_id"],
                ),
            ).rowcount
            if not changed:
                raise DomainError("push_not_subscribed", 409)
        return self.status(session["device_id"])

    def remove(self, device_id):
        with self.database.transaction() as db:
            db.execute("DELETE FROM push_subscription WHERE device_id=?", (device_id,))

    def retry(self, device_id):
        with self.database.transaction() as db:
            row = db.execute(
                "SELECT id FROM push_subscription WHERE device_id=? AND enabled=1", (device_id,)
            ).fetchone()
            if not row:
                raise DomainError("push_not_subscribed", 409)
            return db.execute(
                """UPDATE background_job SET state='queued',attempts=0,error_code=NULL,
                available_at=?,generation=generation+1 WHERE state='failed'
                AND (dedupe_key LIKE ? OR dedupe_key LIKE ?)""",
                (time.time(), f"push.meal:{row['id']}:%", f"push.test:{row['id']}:%"),
            ).rowcount

    def queue_test(self, device_id, request_id):
        with self.database.transaction() as db:
            row = db.execute(
                "SELECT id,preferences FROM push_subscription WHERE device_id=? AND enabled=1",
                (device_id,),
            ).fetchone()
            if not row:
                raise DomainError("push_not_subscribed", 409)
            if not ReminderPreferences.model_validate_json(row["preferences"]).enabled:
                raise DomainError("push_reminders_disabled", 409)
            key = f"push.test:{row['id']}:{request_id}"
            if not db.execute("SELECT 1 FROM background_job WHERE dedupe_key=?", (key,)).fetchone():
                enqueue(db, "notification.test", key, {"subscription_id": row["id"]})

    def has_meals(self, db, day, category):
        return any(
            meal["category"] == category
            and not meal["cooked"]
            and bool(occurrences(Meal.model_validate(meal), day, day))
            for meal in entities(db, "meal").values()
        )

    def enqueue_due(self, now: datetime | None = None):
        now = now or datetime.now(UTC)
        with self.database.transaction() as db:
            household = db.execute("SELECT timezone FROM household WHERE id=1").fetchone()
            if not household:
                return
            # Revoked/expired sign-ins cannot keep receiving meal reminders.
            db.execute(
                """UPDATE push_subscription SET enabled=0,error_code='push_session_expired'
                WHERE session_id IN (SELECT id FROM session WHERE revoked=1 OR refresh_expires<=?)""",
                (now.timestamp(),),
            )
            day = now.astimezone(ZoneInfo(household["timezone"])).date()
            planned_categories = {
                meal["category"]
                for meal in entities(db, "meal").values()
                if not meal["cooked"] and occurrences(Meal.model_validate(meal), day, day)
            }
            for row in db.execute("SELECT * FROM push_subscription WHERE enabled=1").fetchall():
                preferences = ReminderPreferences.model_validate_json(row["preferences"])
                if not preferences.enabled:
                    continue
                for category in CATEGORIES:
                    clock = getattr(preferences, category)
                    if clock is None:
                        continue
                    due = due_at(day, clock, household["timezone"])
                    if not 0 <= (now - due).total_seconds() < GRACE:
                        continue
                    if (
                        category not in planned_categories
                        or db.execute(
                            "SELECT 1 FROM push_delivery WHERE subscription_id=? AND planned_date=? AND category=?",
                            (row["id"], day.isoformat(), category),
                        ).fetchone()
                    ):
                        continue
                    key = f"push.meal:{row['id']}:{day}:{category}"
                    prior = db.execute(
                        "SELECT state FROM background_job WHERE dedupe_key=?", (key,)
                    ).fetchone()
                    if prior is None or prior["state"] == "done":
                        enqueue(
                            db,
                            "notification.meal",
                            key,
                            {"subscription_id": row["id"], "day": str(day), "category": category},
                        )

    def deliver(self, job, now: datetime | None = None):
        now = now or datetime.now(UTC)
        payload = json.loads(job["payload"])
        sid = payload["subscription_id"]
        with self.database.connect() as db:
            row = db.execute(
                """SELECT p.* FROM push_subscription p JOIN session s ON s.id=p.session_id
                WHERE p.id=? AND p.enabled=1 AND s.revoked=0 AND s.refresh_expires>?""",
                (sid, now.timestamp()),
            ).fetchone()
            if not row:
                return
            preferences = ReminderPreferences.model_validate_json(row["preferences"])
            if not preferences.enabled:
                return
            ttl = GRACE
            if job["kind"] == "notification.meal":
                day = date.fromisoformat(payload["day"])
                category = payload["category"]
                clock = getattr(preferences, category)
                zone = db.execute("SELECT timezone FROM household WHERE id=1").fetchone()[0]
                if clock is None:
                    return
                elapsed = (now - due_at(day, clock, zone)).total_seconds()
                if not 0 <= elapsed < GRACE or not self.has_meals(db, day, category):
                    return
                if db.execute(
                    "SELECT 1 FROM push_delivery WHERE subscription_id=? AND planned_date=? AND category=?",
                    (sid, str(day), category),
                ).fetchone():
                    return
                ttl = int(GRACE - elapsed)
                body = (
                    "Dein geplanter Speiseplan wartet auf dich."
                    if row["language"] == "de"
                    else "Your planned meal is waiting for you."
                )
                url = "/app/?tab=calendar&day=" + str(day)
            else:
                body = (
                    "Deine Erinnerungen sind verbunden."
                    if row["language"] == "de"
                    else "Your meal reminders are connected."
                )
                url = "/app/?tab=settings"
            message = {"title": "mealf", "body": body, "url": url, "tag": job["dedupe_key"]}
            credentials = json.loads(self.vault.cipher.decrypt(row["credentials"].encode()))
        try:
            response = self.transport.send(credentials, message, job["dedupe_key"], ttl)
            status = response.status
            if not 200 <= status < 300:
                code = (
                    "push_subscription_expired"
                    if status in (404, 410)
                    else "push_rate_limited"
                    if status == 429
                    else "push_provider_rejected"
                )
                raise PushDeliveryError(code, response.retry_after)
        except DomainError as exc:
            with self.database.transaction() as db:
                db.execute(
                    "UPDATE push_subscription SET error_code=?,enabled=CASE WHEN ?='push_subscription_expired' THEN 0 ELSE enabled END WHERE id=?",
                    (exc.code, exc.code, sid),
                )
            raise
        with self.database.transaction() as db:
            if db.execute("SELECT 1 FROM push_subscription WHERE id=?", (sid,)).fetchone():
                db.execute(
                    "UPDATE push_subscription SET last_success=?,error_code=NULL WHERE id=?",
                    (now.timestamp(), sid),
                )
                if job["kind"] == "notification.meal":
                    db.execute(
                        "INSERT OR IGNORE INTO push_delivery VALUES (?,?,?,?)",
                        (sid, payload["day"], payload["category"], now.timestamp()),
                    )
