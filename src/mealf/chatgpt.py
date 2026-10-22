"""Personal ChatGPT connections are owned by a mealf session, never the household."""

import json
import secrets
import threading
import time
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import httpx
from cryptography.fernet import InvalidToken

from .auth import digest, rate_limit
from .chatgpt_models import ChatGPTDisconnect, ChatGPTPairing, ChatGPTStatus
from .chatgpt_protocol import RESOURCE, ChatGPTProtocol
from .errors import DomainError
from .secrets import SecretVault


class ChatGPTConnections:
    def __init__(self, database, protocol=None):
        self.database = database
        self.protocol = protocol or ChatGPTProtocol()
        self.vault = SecretVault(database.root / "config")
        self.refresh_lock = threading.Lock()
        with database.transaction() as db:
            db.execute(
                "INSERT OR IGNORE INTO chatgpt_host VALUES (1,?)", ("urn:uuid:" + str(uuid4()),)
            )

    def encode(self, value):
        return self.vault.cipher.encrypt(json.dumps(value).encode()).decode()

    def decode(self, value):
        try:
            return json.loads(self.vault.cipher.decrypt(value.encode()))
        except (InvalidToken, ValueError, AttributeError) as exc:
            raise DomainError("chatgpt_reconnect_required", 409) from exc

    @staticmethod
    def require_session(db, sid):
        if not db.execute(
            "SELECT 1 FROM session WHERE id=? AND revoked=0 AND refresh_expires>?",
            (sid, time.time()),
        ).fetchone():
            raise DomainError("chatgpt_session_ended", 409)

    def connection(self, sid, expected=None, ready=True):
        with self.database.connect() as db:
            self.require_session(db, sid)
            row = db.execute(
                "SELECT * FROM chatgpt_connection WHERE session_id=?", (sid,)
            ).fetchone()
        if not row or (expected is not None and row["id"] != expected):
            raise DomainError("chatgpt_connection_changed", 409)
        if ready and (not row["credentials"] or row["error_code"]):
            raise DomainError("chatgpt_reconnect_required", 409)
        return dict(row)

    def status(self, sid):
        with self.database.connect() as db:
            self.require_session(db, sid)
            row = db.execute(
                "SELECT id,label,model,credentials,error_code FROM chatgpt_connection WHERE session_id=?",
                (sid,),
            ).fetchone()
        if not row:
            return ChatGPTStatus(state="disconnected")
        state: Literal["disconnected", "connected", "reconnect_required"] = (
            "reconnect_required"
            if row["error_code"]
            else "connected"
            if row["credentials"]
            else "disconnected"
        )
        return ChatGPTStatus(
            state=state,
            connection_id=row["id"],
            account_label=row["label"],
            model=row["model"],
            error_code=row["error_code"],
        )

    def budget(self, sid, action, maximum=20):
        with self.database.transaction() as db:
            self.require_session(db, sid)
            allowed = rate_limit(db, f"chatgpt.{action}:{sid}", maximum, 3600)
        if not allowed:
            raise DomainError("chatgpt_request_limit", 429)

    def prepare(self, sid):
        self.budget(sid, "pair", 10)
        code, iid, nonce = secrets.token_urlsafe(32), str(uuid4()), secrets.token_urlsafe(32)
        expires = time.time() + 600
        with self.database.transaction() as db:
            self.require_session(db, sid)
            db.execute(
                "DELETE FROM chatgpt_pairing WHERE expires_at<? OR session_id=?", (time.time(), sid)
            )
            row = db.execute(
                "SELECT id FROM chatgpt_connection WHERE session_id=?", (sid,)
            ).fetchone()
            db.execute(
                "INSERT INTO chatgpt_pairing VALUES (?,?,?,?,?,0,?)",
                (iid, sid, digest(code), nonce, expires, row["id"] if row else None),
            )
        return ChatGPTPairing(id=UUID(iid), code=code, expires_at=expires)

    def claim(self, code):
        with self.database.transaction() as db:
            row = db.execute(
                "SELECT * FROM chatgpt_pairing WHERE code_hash=?", (digest(code),)
            ).fetchone()
            if not row or row["expires_at"] <= time.time() or row["claimed"]:
                raise DomainError("chatgpt_pairing_expired", 409)
            self.require_session(db, row["session_id"])
            current = db.execute(
                "SELECT * FROM chatgpt_connection WHERE session_id=?", (row["session_id"],)
            ).fetchone()
            db.execute("UPDATE chatgpt_pairing SET claimed=1 WHERE id=?", (row["id"],))
            host_id = db.execute("SELECT host_id FROM chatgpt_host WHERE slot=1").fetchone()[0]
        credentials = (
            self.decode(current["credentials"]) if current and current["credentials"] else {}
        )
        return {
            "nonce": row["nonce"],
            "client_id": current["client_id"] if current else "dynamic_agent_client",
            "id_token_hint": credentials.get("id_token"),
            "host_id": host_id,
        }

    def complete(self, body):
        code = body.code.get_secret_value()
        with self.database.transaction() as db:
            row = db.execute(
                "SELECT * FROM chatgpt_pairing WHERE code_hash=?", (digest(code),)
            ).fetchone()
            if not row or row["expires_at"] <= time.time() or row["claimed"] != 1:
                raise DomainError("chatgpt_pairing_expired", 409)
            self.require_session(db, row["session_id"])
            prior = db.execute(
                "SELECT * FROM chatgpt_connection WHERE session_id=?", (row["session_id"],)
            ).fetchone()
            if (prior["id"] if prior else None) != row["connection_id"]:
                raise DomainError("chatgpt_connection_changed", 409)
            # One attempt consumes the capability before any external verification.
            db.execute("UPDATE chatgpt_pairing SET claimed=2 WHERE id=?", (row["id"],))
        if prior and body.client_id != prior["client_id"]:
            raise DomainError("chatgpt_identity_invalid", 422)
        raw = body.tokens.model_dump()
        for name in ("access_token", "refresh_token", "id_token"):
            raw[name] = raw[name].get_secret_value()
        credentials, identity = self.protocol.credentials(
            raw, body.client_id, nonce=row["nonce"], subject=prior["subject"] if prior else None
        )
        with self.database.transaction() as db:
            self.require_session(db, row["session_id"])
            pending = db.execute(
                "SELECT * FROM chatgpt_pairing WHERE id=?", (row["id"],)
            ).fetchone()
            if not pending or pending["expires_at"] <= time.time() or pending["claimed"] != 2:
                raise DomainError("chatgpt_pairing_expired", 409)
            db.execute("DELETE FROM chatgpt_pairing WHERE id=?", (row["id"],))
            # New identity invalidates previously approved jobs, including after reconnect.
            db.execute("DELETE FROM chatgpt_connection WHERE session_id=?", (row["session_id"],))
            db.execute(
                "INSERT INTO chatgpt_connection VALUES (?,?,?,?,?,?,?,?,NULL,NULL,?)",
                (
                    str(uuid4()),
                    row["session_id"],
                    body.client_id,
                    identity["subject"],
                    identity["label"],
                    self.encode(credentials),
                    identity["expires_at"],
                    identity["earliest_refresh_at"],
                    time.time(),
                ),
            )
        return self.status(row["session_id"])

    def cancel_pairing(self, sid):
        with self.database.transaction() as db:
            db.execute("DELETE FROM chatgpt_pairing WHERE session_id=?", (sid,))

    def invalidate(self, sid, connection_id, code="chatgpt_reconnect_required"):
        with self.database.transaction() as db:
            db.execute(
                "UPDATE chatgpt_connection SET credentials=NULL,error_code=? WHERE session_id=? AND id=?",
                (code, sid, connection_id),
            )

    def token(self, sid, connection_id):
        # One process owns the DB. Serialize rotating refreshes without holding a SQL
        # transaction while the network is in flight. Disconnect can still clear access.
        with self.refresh_lock:
            row = self.connection(sid, connection_id)
            saved = self.decode(row["credentials"])
            if row["expires_at"] - time.time() > 60:
                return saved["access_token"]
            if row["earliest_refresh_at"] > time.time():
                if row["expires_at"] > time.time() + 5:
                    return saved["access_token"]
                raise DomainError("chatgpt_usage_unavailable", 503)
            try:
                response = self.protocol.json(
                    "POST",
                    self.protocol.discovery()["token_endpoint"],
                    form={
                        "grant_type": "refresh_token",
                        "client_id": row["client_id"],
                        "refresh_token": saved["refresh_token"],
                        "resource": RESOURCE,
                    },
                )
                updated, identity = self.protocol.credentials(
                    response,
                    row["client_id"],
                    previous={**saved, "label": row["label"]},
                    subject=row["subject"],
                )
            except DomainError as exc:
                if exc.code in (
                    "chatgpt_reconnect_required",
                    "chatgpt_identity_invalid",
                    "chatgpt_credentials_invalid",
                    "chatgpt_plan_permission_required",
                ):
                    self.invalidate(sid, connection_id)
                raise
            with self.database.transaction() as db:
                self.require_session(db, sid)
                count = db.execute(
                    "UPDATE chatgpt_connection SET credentials=?,expires_at=?,earliest_refresh_at=?,updated_at=? WHERE session_id=? AND id=? AND credentials=?",
                    (
                        self.encode(updated),
                        identity["expires_at"],
                        identity["earliest_refresh_at"],
                        time.time(),
                        sid,
                        connection_id,
                        row["credentials"],
                    ),
                ).rowcount
                if count != 1:
                    raise DomainError("chatgpt_connection_changed", 409)
            return updated["access_token"]

    def models(self, sid):
        self.budget(sid, "models", 60)
        row = self.connection(sid)
        try:
            result = self.protocol.models(self.token(sid, row["id"]))
            self.connection(sid, row["id"])
            return result
        except DomainError as exc:
            if exc.code == "chatgpt_reconnect_required":
                self.invalidate(sid, row["id"])
            raise

    def select(self, sid, selection):
        row = self.connection(sid, str(selection.connection_id))
        if selection.model not in {m.slug for m in self.models(sid).models}:
            raise DomainError("chatgpt_model_unavailable", 422)
        with self.database.transaction() as db:
            self.require_session(db, sid)
            count = db.execute(
                "UPDATE chatgpt_connection SET model=? WHERE session_id=? AND id=? AND credentials IS NOT NULL",
                (selection.model, sid, row["id"]),
            ).rowcount
            if not count:
                raise DomainError("chatgpt_connection_changed", 409)
        return self.status(sid)

    def extract(self, sid, connection_id, model, text):
        row = self.connection(sid, connection_id)
        if not model or row["model"] != model:
            raise DomainError("chatgpt_configuration_changed", 409)
        self.budget(sid, "imports", 20)
        try:
            result = self.protocol.extract(self.token(sid, connection_id), model, text)
            # Closing the browser is allowed by explicit per-import consent. Session
            # revocation, disconnect and model changes still invalidate late results.
            after = self.connection(sid, connection_id)
            if after["model"] != model:
                raise DomainError("chatgpt_configuration_changed", 409)
            return result
        except DomainError as exc:
            if exc.code == "chatgpt_reconnect_required":
                self.invalidate(sid, connection_id)
            raise

    def disconnect(self, sid):
        with self.database.transaction() as db:
            row = db.execute(
                "SELECT * FROM chatgpt_connection WHERE session_id=?", (sid,)
            ).fetchone()
            db.execute("DELETE FROM chatgpt_pairing WHERE session_id=?", (sid,))
            db.execute(
                "UPDATE chatgpt_connection SET credentials=NULL,error_code=NULL,model=NULL WHERE session_id=?",
                (sid,),
            )
        confirmed = False
        if row and row["credentials"]:
            try:
                value = self.decode(row["credentials"])
                metadata = self.protocol.discovery()
                endpoint = metadata.get("revocation_endpoint", "")
                parsed = urlsplit(endpoint)
                if (
                    parsed.scheme != "https"
                    or parsed.netloc != "auth.openai.com"
                    or parsed.query
                    or parsed.fragment
                ):
                    raise DomainError("chatgpt_discovery_changed", 502)
                with (
                    self.protocol.client() as client,
                    client.stream(
                        "POST",
                        endpoint,
                        data={
                            "token": value["refresh_token"],
                            "token_type_hint": "refresh_token",
                            "client_id": row["client_id"],
                        },
                    ) as response,
                ):
                    confirmed = response.status_code == 200
            except (DomainError, httpx.HTTPError, OSError, ValueError):
                # Sign-out is local even when remote revocation cannot be confirmed.
                pass
        return ChatGPTDisconnect(remote_revocation_confirmed=confirmed)
