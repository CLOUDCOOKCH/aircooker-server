"""PWA sessions: HttpOnly rotating credentials, isolated from console/native clients."""

import hmac
import os
import secrets
import time
from typing import Literal
from uuid import UUID

from fastapi import Depends, Header, Request
from fastapi.responses import JSONResponse, Response

from .auth import authenticate, digest, rate_limit, refresh_session, revoke_refresh_capability
from .errors import DomainError
from .legacy import HEADER_PREFIX, PREFIX, cookie
from .models import Credentials, Model, Setup, Tokens

ACCESS_COOKIE = "mealf_pwa_session"
REFRESH_COOKIE = "mealf_pwa_refresh"
CSRF_COOKIE = "mealf_pwa_csrf"
AUTH_PATH = "/api/v1/pwa/auth"


class BrowserSession(Model):
    authenticated: Literal[True] = True
    session_id: UUID
    device_id: UUID
    expires_in: int


def is_pwa(request: Request) -> bool:
    return (
        request.url.path.startswith(AUTH_PATH + "/")
        or request.headers.get("x-mealf-client") == "pwa"
        or request.headers.get(HEADER_PREFIX + "-client") == "pwa"
    )


def require_origin(request: Request):
    expected = os.environ.get("BASE_URL", "https://localhost").rstrip("/")
    if request.headers.get("origin") != expected:
        raise DomainError("origin_forbidden", 403)


def require_csrf(request: Request, *, pwa: bool):
    csrf_cookie = cookie(request, CSRF_COOKIE if pwa else "mealf_csrf")
    header = request.headers.get("x-csrf-token", "")
    if not csrf_cookie or not hmac.compare_digest(csrf_cookie.encode(), header.encode()):
        raise DomainError("csrf_failed", 403)
    require_origin(request)


def set_session(tokens: Tokens, device_id: UUID, status_code: int = 200) -> JSONResponse:
    response = JSONResponse(
        BrowserSession(
            session_id=tokens.session_id, device_id=device_id, expires_in=tokens.expires_in
        ).model_dump(mode="json"),
        status_code=status_code,
    )
    response.set_cookie(
        ACCESS_COOKIE,
        tokens.access_token,
        max_age=900,
        path="/api/v1",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        tokens.refresh_token,
        max_age=30 * 86400,
        path=AUTH_PATH,
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.set_cookie(
        CSRF_COOKIE, secrets.token_urlsafe(32), secure=True, samesite="strict", path="/"
    )
    clear_legacy_session(response)
    return response


def clear_legacy_session(response):
    for name, path in ((ACCESS_COOKIE, "/api/v1"), (REFRESH_COOKIE, AUTH_PATH), (CSRF_COOKIE, "/")):
        response.delete_cookie(
            name.replace("mealf", PREFIX, 1),
            path=path,
            secure=True,
            httponly=name != CSRF_COOKIE,
            samesite="strict",
        )


def clear_session(response: Response):
    clear_legacy_session(response)
    for name, path in ((ACCESS_COOKIE, "/api/v1"), (REFRESH_COOKIE, AUTH_PATH), (CSRF_COOKIE, "/")):
        response.delete_cookie(
            name, path=path, secure=True, httponly=name != CSRF_COOKIE, samesite="strict"
        )


def register_routes(app, database, login, setup):
    @app.post(AUTH_PATH + "/login", response_model=BrowserSession)
    def browser_login(body: Credentials, request: Request):
        require_origin(request)
        return set_session(login(body, request), body.device_id)

    @app.post(AUTH_PATH + "/setup", status_code=201, response_model=BrowserSession)
    def browser_setup(body: Setup, request: Request, x_setup_token: str = Header(default="")):
        require_origin(request)
        return set_session(setup(body, request, x_setup_token), body.device_id, 201)

    @app.post(AUTH_PATH + "/refresh", response_model=BrowserSession)
    def browser_refresh(request: Request):
        require_csrf(request, pwa=True)
        with database.transaction() as db:
            allowed = rate_limit(
                db,
                "pwa.refresh:" + (request.client.host if request.client else "unknown"),
                maximum=60,
            )
        if not allowed:
            raise DomainError("rate_limited", 429)
        try:
            tokens = refresh_session(database, cookie(request, REFRESH_COOKIE))
        except DomainError as exc:
            response = JSONResponse({"error": {"code": exc.code}}, status_code=exc.status)
            clear_session(response)
            return response
        with database.connect() as db:
            row = db.execute(
                "SELECT device_id FROM session WHERE id=?", (str(tokens.session_id),)
            ).fetchone()
        return set_session(tokens, UUID(row[0]))

    @app.post(AUTH_PATH + "/logout", status_code=204)
    def browser_logout(request: Request):
        require_csrf(request, pwa=True)
        # Refresh-secret capability works when the short-lived access cookie has expired.
        refresh = cookie(request, REFRESH_COOKIE)
        if refresh:
            revoke_refresh_capability(database, refresh)
        access = cookie(request, ACCESS_COOKIE)
        if access:
            with database.transaction() as db:
                db.execute("UPDATE session SET revoked=1 WHERE access_hash=?", (digest(access),))
        response = Response(status_code=204)
        clear_session(response)
        return response

    def current_session(request: Request):
        token = cookie(request, ACCESS_COOKIE)
        with database.connect() as db:
            return authenticate(db, token)

    @app.get(AUTH_PATH + "/session", response_model=BrowserSession)
    def browser_session(row=Depends(current_session)):
        return BrowserSession(
            session_id=row["id"],
            device_id=row["device_id"],
            expires_in=max(0, int(row["access_expires"] - time.time())),
        )
