"""Household accounts. All configuration changes require a live administrator session."""

import sqlite3
import time
from typing import Literal
from uuid import UUID, uuid4

from fastapi import Depends
from pydantic import Field, model_validator

from .auth import hasher, rate_limit
from .errors import DomainError
from .models import Model


class UserInfo(Model):
    id: UUID
    username: str
    role: Literal["admin", "user"]
    active: bool


class UserCreate(Model):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=1024)
    role: Literal["admin", "user"] = "user"


class UserUpdate(Model):
    username: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=12, max_length=1024)
    role: Literal["admin", "user"] | None = None
    active: bool | None = None

    @model_validator(mode="after")
    def nonempty_patch(self):
        if not self.model_fields_set or any(
            getattr(self, key) is None for key in self.model_fields_set
        ):
            raise ValueError("Provide a non-null account change")
        return self


def require_admin(current):
    if current["role"] != "admin":
        raise DomainError("admin_required", 403)


def public_user(row):
    return {key: row[key] for key in ("id", "username", "role", "active")}


def check_admin_transaction(db, current):
    # A reset/demotion can race an expensive password hash. Recheck under the writer lock.
    actor = db.execute(
        "SELECT u.role FROM session s JOIN household_user u ON u.id=s.user_id "
        "WHERE s.id=? AND s.revoked=0 AND s.access_expires>? AND s.refresh_expires>? AND u.active=1",
        (current["id"], time.time(), time.time()),
    ).fetchone()
    if actor is None:
        raise DomainError("authentication_required", 401)
    require_admin(actor)


def register_routes(app, session, database):
    def admin(current=Depends(session)):
        require_admin(current)
        return current

    @app.get("/api/v1/auth/me", response_model=UserInfo)
    def me(current=Depends(session)):
        with database.connect() as db:
            return public_user(
                db.execute(
                    "SELECT * FROM household_user WHERE id=?", (current["user_id"],)
                ).fetchone()
            )

    @app.get("/api/v1/admin/users", response_model=list[UserInfo])
    def users(current=Depends(admin)):
        with database.connect() as db:
            return [
                public_user(row)
                for row in db.execute("SELECT * FROM household_user ORDER BY username")
            ]

    def admission(current):
        with database.transaction() as db:
            allowed = rate_limit(db, "user-management:" + current["id"], 60, 3600)
        if not allowed:
            raise DomainError("rate_limited", 429)

    @app.post("/api/v1/admin/users", response_model=UserInfo, status_code=201)
    def create(body: UserCreate, current=Depends(admin)):
        admission(current)
        uid = str(uuid4())
        password_hash = hasher.hash(body.password)
        try:
            with database.transaction() as db:
                check_admin_transaction(db, current)
                if db.execute("SELECT COUNT(*) FROM household_user").fetchone()[0] >= 100:
                    raise DomainError("household_user_limit", 409)
                db.execute(
                    "INSERT INTO household_user VALUES (?,?,?,?,1)",
                    (uid, body.username, password_hash, body.role),
                )
        except sqlite3.IntegrityError as exc:
            raise DomainError("username_taken", 409) from exc
        return UserInfo(id=UUID(uid), username=body.username, role=body.role, active=True)

    @app.patch("/api/v1/admin/users/{user_id}", response_model=UserInfo)
    def update(user_id: UUID, body: UserUpdate, current=Depends(admin)):
        admission(current)
        password_hash = hasher.hash(body.password) if body.password is not None else None
        try:
            with database.transaction() as db:
                check_admin_transaction(db, current)
                row = db.execute(
                    "SELECT * FROM household_user WHERE id=?", (str(user_id),)
                ).fetchone()
                if row is None:
                    raise DomainError("user_not_found", 404)
                changed = {**dict(row), **body.model_dump(exclude_unset=True, exclude={"password"})}
                if (
                    row["active"]
                    and row["role"] == "admin"
                    and (not changed["active"] or changed["role"] != "admin")
                ):
                    if (
                        db.execute(
                            "SELECT COUNT(*) FROM household_user WHERE active=1 AND role='admin'"
                        ).fetchone()[0]
                        <= 1
                    ):
                        raise DomainError("last_admin_required", 409)
                db.execute(
                    "UPDATE household_user SET username=?,password_hash=?,role=?,active=? WHERE id=?",
                    (
                        changed["username"],
                        password_hash or row["password_hash"],
                        changed["role"],
                        changed["active"],
                        str(user_id),
                    ),
                )
                # Password/identity/privilege changes invalidate all of this account's capabilities.
                if password_hash or any(
                    changed[key] != row[key] for key in ("username", "role", "active")
                ):
                    db.execute("UPDATE session SET revoked=1 WHERE user_id=?", (str(user_id),))
                return public_user(changed)
        except sqlite3.IntegrityError as exc:
            raise DomainError("username_taken", 409) from exc
