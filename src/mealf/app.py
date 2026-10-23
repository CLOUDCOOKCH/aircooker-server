import asyncio
import hmac
import json
import logging
import os
import secrets
import shutil
import sqlite3
import tempfile
import time
from contextlib import asynccontextmanager, suppress
from datetime import date, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, File, Header, Query, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from starlette.background import BackgroundTask

from . import __version__, recipe_ideas
from .ai import provider_for
from .ai_settings import (
    AIProviderCatalog,
    AISettings,
    AISettingsStatus,
    load_configuration,
    provider_catalog,
    save_configuration,
    settings_status,
)
from .auth import (
    DUMMY_HASH,
    authenticate,
    hasher,
    new_session,
    rate_limit,
    refresh_session,
    revoke_refresh_capability,
    verify_password,
)
from .backup import (
    MAX_ARCHIVE,
    MAX_JSON_EXPORT,
    HouseholdExport,
    export_archive,
    export_household,
    import_archive,
    import_household,
)
from .bring import reconcile
from .bring_runtime import UnofficialBringConnector
from .bring_verification import verify as verify_bring
from .chatgpt import ChatGPTConnections
from .chatgpt_routes import register_routes as register_chatgpt
from .db import Database
from .diagnostics import diagnostics, public_error, recent_jobs
from .errors import DomainError
from .food_profile import register_routes as register_food_profile
from .image_import import ocr_available, recognise_text
from .import_receipts import fingerprint as import_fingerprint
from .import_sources import ImportSourceInfo, put_source
from .importing import bounded_fetch_page, extract, platform_for
from .instance_lock import InstanceLock
from .jobs import claim, enqueue, finish
from .legacy import HEADER_PREFIX, PREFIX, cookie
from .media import MAX_UPLOAD_BYTES, MediaInfo, info_for, put_media
from .models import (
    AdministrationDiagnostics,
    AdministrationStatus,
    BringConfiguration,
    BringCredentials,
    Credentials,
    HouseholdSettings,
    ImportRequest,
    JobInfo,
    Mutation,
    MutationResult,
    PasswordChange,
    Pull,
    Push,
    RecipeImportStatus,
    Refresh,
    SessionInfo,
    Setup,
    SuggestionApply,
    SuggestionPreview,
    SyncAnchor,
    SyncSnapshot,
    SyncState,
    Tokens,
)
from .planning import entities, occurrences, shopping_projection, week_start
from .planning_preferences import context as planning_context
from .planning_preferences import register_routes as register_planning_preferences
from .pwa_auth import ACCESS_COOKIE, is_pwa, require_csrf
from .pwa_auth import register_routes as register_pwa_auth
from .quantities import PlanningServings
from .recipe_imports import process_import
from .recommendations import planning_basis, suggest_week
from .reminder_routes import register_routes as register_reminders
from .reminders import Reminders
from .retention import cleanup_database, cleanup_startup_transfers
from .secrets import SecretVault
from .shopping import BringVerification, ShoppingSnapshot, request_verification
from .shopping import snapshot as shopping_snapshot
from .source_images import bounded_source_photo
from .suggestion_apply import apply_preview
from .sync import active, apply_mutation, pull
from .sync_history import snapshot_page, state_for, validate_anchor
from .users import register_routes as register_users
from .users import require_admin

bearer = HTTPBearer(auto_error=False)


def create_app(data_dir: Path | None = None, run_worker: bool = True):
    data_dir = data_dir or Path(os.environ.get("DATA_DIR", "/data"))
    lease = InstanceLock(data_dir) if run_worker else None
    try:
        if (data_dir / ".household-deletion.json").exists():
            raise RuntimeError(
                "Household deletion is incomplete; resume the offline deletion command"
            )
        return _create_app(data_dir, run_worker, lease)
    except BaseException:
        if lease:
            lease.close()
        raise


def _create_app(data_dir: Path, run_worker: bool, lease: InstanceLock | None):
    data_dir = data_dir or Path(os.environ.get("DATA_DIR", "/data"))
    database = Database(data_dir)
    cleanup_startup_transfers(data_dir)
    media_slots = asyncio.Semaphore(2)
    archive_slots = asyncio.Semaphore(1)
    SecretVault(data_dir / "config")
    reminders = Reminders(database, data_dir / "config")
    chatgpt = ChatGPTConnections(database)
    token_file = data_dir / "config" / "setup-token"
    with database.connect() as db:
        configured = db.execute("SELECT 1 FROM household").fetchone()
    if not configured and not token_file.exists():
        try:
            fd = os.open(token_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w") as out:
                out.write(secrets.token_urlsafe(48))
        except FileExistsError:
            pass

    def process_job(job):
        payload = json.loads(job["payload"])
        if job["kind"] in ("notification.meal", "notification.test"):
            reminders.deliver(job)
            return
        if job["kind"] == "bring.verify":
            verify_bring(database, UnofficialBringConnector, payload["id"])
            return
        if job["kind"] == "shopping.reconcile":
            with database.connect() as db:
                household = db.execute("SELECT * FROM household").fetchone()
                if household:
                    today = datetime.now(ZoneInfo(household["timezone"])).date()
                    monday = week_start(today)
                    desired = shopping_projection(db, monday)
                else:
                    return
            raw = SecretVault(data_dir / "config").load("bring")
            if not raw:
                return
            settings = json.loads(raw)
            if not settings.get("list_id"):
                raise DomainError("bring_list_not_selected", 409)
            with UnofficialBringConnector(data_dir / "config") as connector:
                reconcile(database, connector, settings["list_id"], str(monday), desired)
            return
        if job["kind"] == "recipe.ideas":
            recipe_ideas.process(database, payload, provider_for)
            return
        if job["kind"] == "recipe.import":
            process_import(
                database,
                payload,
                fetch=bounded_fetch_page,
                source_photo=bounded_source_photo,
                provider_factory=provider_for,
                extractor=extract,
                recognise=recognise_text,
                personal_extract=chatgpt.extract,
            )
            return
        raise DomainError("unknown_job_kind")

    async def durable_work(function, *args, **kwargs):
        # Cancelling to_thread does not stop its thread. Keep the volume lease
        # until in-flight maintenance/job writes have actually finished.
        task = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            with suppress(Exception):
                await task
            raise

    async def worker():
        last_periodic = 0.0
        last_cleanup = -3600.0
        while True:
            try:
                if time.monotonic() - last_cleanup >= 3600:
                    try:
                        counts = await durable_work(cleanup_database, database)
                        if any(counts.values()):
                            logging.getLogger(__name__).info(
                                json.dumps({"event": "maintenance_cleanup", "counts": counts})
                            )
                    except Exception:
                        logging.getLogger(__name__).warning(
                            '{"event":"maintenance_cleanup_failed"}'
                        )
                    last_cleanup = time.monotonic()
                if time.monotonic() - last_periodic > 60:
                    await durable_work(reminders.enqueue_due)
                    with database.transaction() as db:
                        prior = db.execute(
                            "SELECT state FROM background_job WHERE dedupe_key='shopping.current'"
                        ).fetchone()
                        if prior is None or prior[0] == "done":
                            enqueue(db, "shopping.reconcile", "shopping.current", {})
                    last_periodic = time.monotonic()
                job = await durable_work(claim, database)
                if job:
                    try:
                        await durable_work(process_job, job)
                    except Exception as exc:
                        code = exc.code if isinstance(exc, DomainError) else "job_processing_failed"
                        await durable_work(
                            finish,
                            database,
                            job,
                            code,
                            retry_after=getattr(exc, "retry_after", None),
                            terminal=getattr(exc, "terminal", False),
                        )
                    else:
                        await durable_work(finish, database, job)
                else:
                    await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Storage/transient failures during claim or finish must not kill
                # the only durable worker. Running leases remain replayable.
                logging.getLogger(__name__).warning('{"event":"worker_retry"}')
                await asyncio.sleep(2)

    @asynccontextmanager
    async def lifespan(app):
        # Explicit operator-requested exception to credential redaction: only the
        # one-time bootstrap token, only on startup while no household exists.
        # Keep this out of factory construction (e.g. OpenAPI generation) and HTTP logs.
        if os.environ.get("LOG_SETUP_TOKEN", "true").strip().lower() in {"1", "true", "yes"}:
            with database.connect() as db:
                if not db.execute("SELECT 1 FROM household").fetchone():
                    try:
                        setup_token = token_file.read_text().strip()
                    except FileNotFoundError:
                        setup_token = ""  # Another bootstrap may have just completed.
                    if setup_token:
                        print(
                            json.dumps(
                                {
                                    "event": "setup_required",
                                    "message": "Use this one-time token to finish mealf setup.",
                                    "setup_token": setup_token,
                                }
                            ),
                            flush=True,
                        )
        task = asyncio.create_task(worker()) if run_worker else None
        try:
            yield
        finally:
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            if lease:
                lease.close()

    app = FastAPI(
        title="mealf server",
        version=__version__,
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.database = database
    app.state.process_job = process_job

    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse({"error": {"code": exc.code}}, status_code=exc.status)

    @app.exception_handler(sqlite3.OperationalError)
    async def storage_error(request, exc):
        # A failed transaction keeps the client's mutation pending. Never echo SQL,
        # household content or paths, including on a physically full data volume.
        unavailable = getattr(exc, "sqlite_errorcode", 0) & 0xFF in {
            sqlite3.SQLITE_FULL,
            sqlite3.SQLITE_IOERR,
            sqlite3.SQLITE_CANTOPEN,
        }
        code = "storage_unavailable" if unavailable else "database_operation_failed"
        logging.getLogger(__name__).warning(json.dumps({"event": code}))
        return JSONResponse({"error": {"code": code}}, status_code=503 if unavailable else 500)

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(ValidationError)
    async def invalid_input(request, exc):
        # Do not echo submitted passwords, source content or tokens.
        return JSONResponse({"error": {"code": "validation_failed"}}, status_code=422)

    @app.middleware("http")
    async def security(request: Request, call_next):
        image_upload = request.method == "PUT" and request.url.path.startswith(
            ("/api/v1/media/", "/api/v1/import-sources/")
        )
        archive_upload = (
            request.method == "POST" and request.url.path == "/api/v1/admin/import/archive"
        )
        json_restore = request.method == "POST" and request.url.path == "/api/v1/admin/import"
        body_limit = (
            MAX_ARCHIVE
            if archive_upload
            else (
                (MAX_UPLOAD_BYTES + 65536)
                if image_upload
                else (MAX_JSON_EXPORT if json_restore else 1_500_000)
            )
        )
        try:
            too_large = int(request.headers.get("content-length", "0")) > body_limit
        except ValueError:
            too_large = True
        if too_large:
            return JSONResponse({"error": {"code": "request_too_large"}}, status_code=413)
        # Authenticate large transfers before reading/parsing their bodies. Browser CSRF
        # validation is the same as every other authenticated mutation.
        if (
            image_upload
            or archive_upload
            or json_restore
            or (
                request.url.path.startswith("/api/v1/admin/")
                and request.url.path != "/api/v1/admin/login"
            )
        ):
            try:
                session(request, await bearer(request))
            except DomainError as exc:
                return JSONResponse({"error": {"code": exc.code}}, status_code=exc.status)

        async def bounded_request():
            if not archive_upload and request.method in ("POST", "PUT", "PATCH"):
                body = bytearray()
                async for chunk in request.stream():
                    body.extend(chunk)
                    if len(body) > body_limit:
                        return JSONResponse(
                            {"error": {"code": "request_too_large"}}, status_code=413
                        )
                request._body = bytes(body)
            return await call_next(request)

        if archive_upload:
            async with archive_slots:
                response = await bounded_request()
        elif image_upload or json_restore:
            async with media_slots:
                response = await bounded_request()
        else:
            response = await bounded_request()
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        response.headers["Cache-Control"] = "no-store"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    def session(
        request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
    ):
        token = (
            credentials.credentials
            if credentials
            else cookie(request, ACCESS_COOKIE if is_pwa(request) else "mealf_session")
        )
        if not token:
            raise DomainError("authentication_required", 401)
        if not credentials and request.method not in ("GET", "HEAD", "OPTIONS"):
            require_csrf(request, pwa=is_pwa(request))
        with database.connect() as db:
            current = authenticate(db, token)
        path = request.url.path
        if (
            path.startswith("/api/v1/admin/")
            or (path == "/api/v1/household" and request.method == "PUT")
            or path
            in {
                "/api/v1/integrations/bring/connect",
                "/api/v1/integrations/bring/lists",
                "/api/v1/integrations/bring/configuration",
                "/api/v1/integrations/bring/disconnect",
                "/api/v1/integrations/bring/verify",
            }
        ):
            require_admin(current)
        return current

    register_users(app, session, database)
    register_reminders(app, session, reminders)
    register_chatgpt(app, session, chatgpt)
    app.state.chatgpt = chatgpt
    app.state.reminders = reminders
    register_planning_preferences(app, session, database)
    register_food_profile(app, session, database)

    @app.get("/api/v1/system/info")
    def info():
        with database.connect() as db:
            h = db.execute("SELECT name,instance_id FROM household").fetchone()
        return {
            "name": h["name"] if h else "mealf",
            "instance_id": h["instance_id"] if h else None,
            "version": __version__,
            "api_major": 1,
            "sync_protocol": 1,
            "configured": bool(h),
        }

    @app.get("/api/v1/system/health")
    def health():
        with database.connect() as db:
            healthy = db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        return JSONResponse(
            {"status": "ok" if healthy else "unhealthy"}, status_code=200 if healthy else 503
        )

    @app.get("/api/v1/system/capabilities")
    def capabilities():
        bring_automatic = False
        if SecretVault(data_dir / "config").load("bring"):
            connector = UnofficialBringConnector(data_dir / "config")
            bring_automatic = connector.capabilities.uuid_create
            connector.runner.close()
        return {
            "sync": True,
            "sync_history_proof": 1,
            "recipe_crud": True,
            "structured_import_preview": True,
            "chatgpt_personal_text": True,
            "bring_automatic_mutations": bring_automatic,
            "shopping_view": True,
            "ai": settings_status(data_dir / "config").enabled,
            "media_upload": True,
            "image_recipe_import": ocr_available(),
            "image_import_languages": ["en", "de"] if ocr_available() else [],
        }

    @app.post("/api/v1/setup", status_code=201, response_model=Tokens)
    def setup(body: Setup, request: Request, x_setup_token: str = Header(default="")):
        with database.transaction() as db:
            allowed = rate_limit(
                db, "setup:" + (request.client.host if request.client else "unknown"), maximum=5
            )
        if not allowed:
            raise DomainError("rate_limited", 429)
        with database.transaction() as db:
            if db.execute("SELECT 1 FROM household").fetchone():
                raise DomainError("setup_locked", 409)
            if not token_file.exists() or not hmac.compare_digest(
                x_setup_token, token_file.read_text().strip()
            ):
                raise DomainError("invalid_setup_token", 403)
            db.execute(
                "INSERT INTO household VALUES (1,?,?,?,?,?,?)",
                (
                    body.name,
                    body.timezone,
                    body.language,
                    body.username,
                    hasher.hash(body.password),
                    str(uuid4()),
                ),
            )
            household = db.execute("SELECT instance_id,password_hash FROM household").fetchone()
            db.execute(
                "INSERT INTO household_user VALUES (?,?,?,?,1)",
                (household[0], body.username, household[1], "admin"),
            )
            result = new_session(db, str(body.device_id), user_id=household[0])
        token_file.unlink(missing_ok=True)
        return result

    def login(body: Credentials, request: Request, *, admin_only: bool = False):
        with database.transaction() as db:
            allowed = rate_limit(
                db, "login:" + (request.client.host if request.client else "unknown")
            )
            # An IP already denied admission must not drain other devices' budget.
            global_allowed = allowed and rate_limit(db, "login:household", maximum=30)
        if not allowed or not global_allowed:
            raise DomainError("rate_limited", 429)
        with database.transaction() as db:
            h = db.execute(
                "SELECT * FROM household_user WHERE username=?", (body.username,)
            ).fetchone()
            valid = verify_password(body.password, h["password_hash"] if h else DUMMY_HASH)
            if (
                not h
                or not valid
                or not h["active"]
                or not hmac.compare_digest(body.username.encode(), h["username"].encode())
            ):
                raise DomainError("invalid_credentials", 401)
            if admin_only:
                require_admin(h)
            return new_session(db, str(body.device_id), user_id=h["id"])

    @app.post(
        "/api/v1/auth/login", response_model=Tokens, operation_id="login_api_v1_auth_login_post"
    )
    def token_login(body: Credentials, request: Request):
        return login(body, request)

    @app.post("/api/v1/auth/refresh", response_model=Tokens)
    def refresh(body: Refresh):
        return refresh_session(database, body.refresh_token)

    @app.post("/api/v1/auth/revoke", status_code=204)
    def revoke_capability(body: Refresh, request: Request):
        # Capability authentication, not browser cookies. Never accept a session UUID.
        with database.transaction() as db:
            allowed = rate_limit(
                db,
                "revoke:" + (request.client.host if request.client else "unknown"),
                maximum=60,
            )
        if not allowed:
            raise DomainError("rate_limited", 429)
        revoke_refresh_capability(database, body.refresh_token)

    @app.post("/api/v1/auth/logout", status_code=204)
    def logout(s=Depends(session)):
        with database.transaction() as db:
            db.execute("UPDATE session SET revoked=1 WHERE id=?", (s["id"],))

    @app.get("/api/v1/auth/sessions", response_model=list[SessionInfo])
    def sessions(s=Depends(session)):
        with database.connect() as db:
            return [
                {**dict(r), "current": r["id"] == s["id"]}
                for r in db.execute(
                    "SELECT id,device_id,access_expires,refresh_expires,revoked FROM session WHERE user_id=? OR ?='admin'",
                    (s["user_id"], s["role"]),
                )
            ]

    @app.delete("/api/v1/auth/sessions/{session_id}", status_code=204)
    def revoke(session_id: UUID, s=Depends(session)):
        with database.transaction() as db:
            db.execute(
                "UPDATE session SET revoked=1 WHERE id=? AND (user_id=? OR ?='admin')",
                (str(session_id), s["user_id"], s["role"]),
            )

    @app.post("/api/v1/sync/push", response_model=list[MutationResult])
    def push(body: Push, s=Depends(session)):
        with database.transaction() as db:
            if body.checkpoint is not None:
                validate_anchor(db, body.checkpoint)
            return [apply_mutation(db, m, s["device_id"]) for m in body.mutations]

    @app.get("/api/v1/sync/pull", response_model=Pull)
    def sync_pull(
        cursor: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=500),
        token: str | None = Query(default=None, pattern=r"^(root|[a-f0-9]{32})$"),
        s=Depends(session),
    ):
        with database.connect() as db:
            db.execute("BEGIN")
            if token is not None:
                validate_anchor(db, SyncAnchor(cursor=cursor, token=token))
            high = db.execute("SELECT COALESCE(MAX(sequence),0) FROM change_log").fetchone()[0]
            if cursor > high:
                raise DomainError("cursor_ahead_of_server_full_resync_required", 409)
            return pull(db, cursor, limit)

    @app.get("/api/v1/sync/state", response_model=SyncState)
    def sync_state(cursor: int = Query(default=0, ge=0), s=Depends(session)):
        with database.connect() as db:
            return state_for(db, cursor)

    @app.get("/api/v1/sync/snapshot", response_model=SyncSnapshot)
    def sync_snapshot(
        cursor: int = Query(ge=0),
        token: str = Query(pattern=r"^(root|[a-f0-9]{32})$"),
        after: str = Query(default="", max_length=50),
        limit: int = Query(default=100, ge=1, le=100),
        s=Depends(session),
    ):
        with database.connect() as db:
            return snapshot_page(db, SyncAnchor(cursor=cursor, token=token), after, limit)

    def resource_routes(kind, route):
        @app.get(route, operation_id=f"list_{kind}")
        def listing(
            after: str = "", limit: int = Query(default=50, ge=1, le=200), s=Depends(session)
        ):
            with database.connect() as db:
                rows = list(
                    db.execute(
                        "SELECT * FROM entity WHERE kind=? AND deleted=0 AND id>? ORDER BY id LIMIT ?",
                        (kind, after, limit + 1),
                    )
                )
            items = [
                {
                    "id": r["id"],
                    "revision": r["revision"],
                    "updated_at": r["updated_at"],
                    "payload": json.loads(r["payload"]),
                }
                for r in rows[:limit]
            ]
            return {"items": items, "next": items[-1]["id"] if len(rows) > limit else None}

        @app.get(route + "/{entity_id}", operation_id=f"get_{kind}")
        def get_entity(entity_id: UUID, s=Depends(session)):
            with database.connect() as db:
                row = active(db, kind, entity_id)
            if not row:
                raise DomainError("not_found", 404)
            return {
                "id": row["id"],
                "revision": row["revision"],
                "payload": json.loads(row["payload"]),
            }

        @app.post(
            route, status_code=201, response_model=MutationResult, operation_id=f"create_{kind}"
        )
        def create_entity(body: Mutation, s=Depends(session)):
            if body.kind != kind or body.operation != "upsert" or body.base_revision != 0:
                raise DomainError("invalid_resource_mutation")
            with database.transaction() as db:
                # A repeated request may replay its own mutation, but may not clobber another entity.
                if (
                    active(db, kind, body.entity_id)
                    and not db.execute(
                        "SELECT 1 FROM mutation WHERE id=?", (str(body.mutation_id),)
                    ).fetchone()
                ):
                    raise DomainError("entity_already_exists", 409)
                return apply_mutation(db, body, s["device_id"])

        @app.patch(
            route + "/{entity_id}", response_model=MutationResult, operation_id=f"update_{kind}"
        )
        def update_entity(entity_id: UUID, body: Mutation, s=Depends(session)):
            if body.kind != kind or body.entity_id != entity_id or body.operation != "upsert":
                raise DomainError("invalid_resource_mutation")
            with database.transaction() as db:
                return apply_mutation(db, body, s["device_id"])

        @app.delete(
            route + "/{entity_id}", response_model=MutationResult, operation_id=f"delete_{kind}"
        )
        def delete_entity(entity_id: UUID, body: Mutation, s=Depends(session)):
            if body.kind != kind or body.entity_id != entity_id or body.operation != "delete":
                raise DomainError("invalid_resource_mutation")
            with database.transaction() as db:
                return apply_mutation(db, body, s["device_id"])

    for kind, route in [
        ("recipe", "recipes"),
        ("meal", "calendar/meals"),
        ("pantry", "pantry"),
        ("leftover", "leftovers"),
        ("template", "templates"),
    ]:
        resource_routes(kind, "/api/v1/" + route)

    @app.get("/api/v1/calendar")
    def calendar(start: date, end: date, s=Depends(session)):
        from .models import Meal

        if end < start or (end - start).days > 366:
            raise DomainError("invalid_calendar_window")
        with database.connect() as db:
            meals = entities(db, "meal")
        return [
            {"id": mid, "occurrence_date": str(day), "payload": raw}
            for mid, raw in meals.items()
            for day in occurrences(Meal.model_validate(raw), start, end)
        ]

    @app.get("/api/v1/planning/shopping-projection")
    def projection(s=Depends(session)):
        with database.connect() as db:
            h = db.execute("SELECT timezone FROM household").fetchone()
            monday = week_start(datetime.now(ZoneInfo(h[0])).date())
            return {
                "period": str(monday),
                "requirements": list(shopping_projection(db, monday).values()),
            }

    @app.get("/api/v1/planning/shopping", response_model=ShoppingSnapshot)
    def shopping(s=Depends(session)):
        return shopping_snapshot(database, UnofficialBringConnector)

    @app.post("/api/v1/integrations/bring/verify", status_code=202)
    def bring_verify(body: BringVerification, s=Depends(session)):
        return request_verification(database, body)

    @app.post("/api/v1/suggestions/weekly", response_model=SuggestionPreview)
    def suggestions(
        monday: date,
        seed: int = Query(default=0, ge=0, le=2147483647),
        categories: list[Literal["breakfast", "lunch", "dinner"]] | None = Query(
            default=None, min_length=1, max_length=3
        ),
        allow_repeats: bool | None = None,
        servings: PlanningServings | None = None,
        s=Depends(session),
    ):
        with database.connect() as db:
            db.execute("BEGIN")
            start = week_start(monday)
            preferences = planning_context(db).preferences
            return SuggestionPreview(
                monday=start,
                basis=planning_basis(db),
                meals=suggest_week(
                    db,
                    start,
                    seed,
                    categories if categories is not None else preferences.categories,
                    allow_repeats if allow_repeats is not None else preferences.allow_repeats,
                    servings if servings is not None else preferences.servings,
                    use_leftovers=preferences.use_leftovers,
                ),
            )

    @app.post("/api/v1/suggestions/apply", response_model=list[MutationResult])
    def approve_suggestions(body: SuggestionApply, s=Depends(session)):
        return apply_preview(database, body, s["device_id"])

    @app.get("/api/v1/ai/status", response_model=AISettingsStatus)
    @app.get("/api/v1/admin/ai", response_model=AISettingsStatus)
    def ai_settings(s=Depends(session)):
        return settings_status(data_dir / "config")

    @app.get("/api/v1/admin/ai/providers", response_model=AIProviderCatalog)
    def ai_profiles(s=Depends(session)):
        return provider_catalog(data_dir / "config")

    @app.put("/api/v1/admin/ai", response_model=AISettingsStatus)
    def configure_ai(body: AISettings, s=Depends(session)):
        return save_configuration(data_dir / "config", body)

    @app.post("/api/v1/admin/ai/test")
    def test_ai(s=Depends(session)):
        config = load_configuration(data_dir / "config")
        if config is None:
            raise DomainError("ai_not_configured", 409)
        with database.transaction() as db:
            allowed = rate_limit(db, "ai.test", maximum=5, seconds=60)
            if allowed:
                allowed = rate_limit(
                    db, "ai.requests", maximum=config.requests_per_hour, seconds=3600
                )
        if not allowed:
            raise DomainError("ai_test_rate_limited", 429)
        provider = provider_for(config)
        try:
            provider.extract_recipe(
                "Recipe: Connection test soup. Serves 2. Ingredient: 200 g carrots. Instruction: Simmer carrots in water until tender. No nutrition data available."
            )
        except DomainError as exc:
            # This endpoint validates a saved configuration. A provider failure is a
            # failed validation, not evidence that this HTTP server is a bad gateway.
            # Keeping it 4xx preserves its diagnostic body through 5xx error pages.
            code = public_error(exc.code) or "operation_failed"
            logging.getLogger(__name__).warning(
                json.dumps({"event": "ai_connection_test_failed", "error_code": code})
            )
            raise DomainError(code, 422 if exc.status >= 500 else exc.status) from exc
        finally:
            provider.close()
        return {"state": "validated_probe_response", "household_content_sent": False}

    @app.get("/api/v1/integrations/bring/status")
    def bring_status(s=Depends(session)):
        raw = SecretVault(data_dir / "config").load("bring")
        if not raw:
            return {"state": "not_configured", "automatic_mutations": False}
        connector = UnofficialBringConnector(data_dir / "config")
        verified = connector.capabilities.uuid_create
        connector.runner.close()
        return {
            "state": "configured" if verified else "compatibility_unverified",
            "list_id": json.loads(raw).get("list_id"),
            "automatic_mutations": verified,
        }

    @app.post("/api/v1/integrations/bring/connect")
    def connect_bring(body: BringCredentials, s=Depends(session)):
        # Credentials are encrypted separately from all normal household records.
        # Authentication is tested through the explicit read-only list operation.
        SecretVault(data_dir / "config").save(
            "bring", json.dumps({"email": body.email, "password": body.password})
        )
        return {"state": "credentials_saved", "authentication": "unverified"}

    @app.get("/api/v1/integrations/bring/lists")
    def bring_lists(s=Depends(session)):
        try:
            with UnofficialBringConnector(data_dir / "config") as connector:
                return {"lists": connector.lists()}
        except DomainError:
            raise
        except Exception as exc:
            raise DomainError("bring_connection_failed", 502) from exc

    @app.put("/api/v1/integrations/bring/configuration")
    def configure_bring(body: BringConfiguration, s=Depends(session)):
        vault = SecretVault(data_dir / "config")
        raw = vault.load("bring")
        if not raw:
            raise DomainError("bring_not_configured", 409)
        settings = json.loads(raw)
        # Re-check list membership; never accept an arbitrary foreign list ID.
        try:
            with UnofficialBringConnector(data_dir / "config") as connector:
                available = connector.lists()
        except Exception as exc:
            raise DomainError("bring_connection_failed", 502) from exc
        if str(body.list_id) not in {item["id"] for item in available}:
            raise DomainError("bring_list_not_found", 404)
        settings["list_id"] = str(body.list_id)
        settings["list_name"] = next(
            item["name"] for item in available if item["id"] == str(body.list_id)
        )
        vault.save("bring", json.dumps(settings))
        with database.transaction() as db:
            enqueue(db, "shopping.reconcile", "shopping.current", {})
        return {"state": "selected", "compatibility_verification_required": True}

    @app.delete("/api/v1/integrations/bring/disconnect", status_code=204)
    def disconnect_bring(s=Depends(session)):
        SecretVault(data_dir / "config").remove("bring")
        (data_dir / "config" / "bring-compatibility.json").unlink(missing_ok=True)

    @app.post("/api/v1/integrations/bring/reconcile", status_code=202)
    def bring_retry(s=Depends(session)):
        with database.transaction() as db:
            enqueue(db, "shopping.reconcile", "shopping.current", {})
        return {"state": "queued", "external_sync": "pending"}

    @app.put("/api/v1/import-sources/{source_id}", response_model=ImportSourceInfo)
    async def upload_import_source(
        source_id: UUID, file: UploadFile = File(...), s=Depends(session)
    ):
        try:
            with database.transaction() as db:
                allowed = rate_limit(db, "import.uploads", maximum=40, seconds=3600)
            if not allowed:
                raise DomainError("import_rate_limited", 429)
            raw = await file.read(MAX_UPLOAD_BYTES + 1)
            return await durable_work(put_source, database, source_id, raw, file.content_type or "")
        finally:
            await file.close()

    @app.post("/api/v1/recipe-ideas", response_model=recipe_ideas.IdeaStatus, status_code=202)
    def generate_recipe_ideas(body: recipe_ideas.IdeaRequest, s=Depends(session)):
        return recipe_ideas.start(database, body)

    @app.get("/api/v1/recipe-ideas/{request_id}", response_model=recipe_ideas.IdeaStatus)
    def read_recipe_ideas(request_id: UUID, s=Depends(session)):
        return recipe_ideas.status(database, request_id)

    @app.post("/api/v1/imports", status_code=202)
    def start_import(body: ImportRequest, s=Depends(session)):
        iid = str(body.request_id)
        with database.connect() as db:
            receipt = db.execute(
                "SELECT state,request_fingerprint FROM import_draft WHERE id=?", (iid,)
            ).fetchone()
        if receipt and receipt["request_fingerprint"] is not None:
            with database.connect() as db:
                owner = db.execute(
                    "SELECT session_id FROM chatgpt_import WHERE import_id=?", (iid,)
                ).fetchone()
            if owner and owner["session_id"] != s["id"]:
                raise DomainError("chatgpt_import_owner_mismatch", 403)
            if receipt["request_fingerprint"] != import_fingerprint(body.model_dump(mode="json")):
                raise DomainError("idempotency_conflict", 409)
            return {"id": iid, "state": receipt["state"]}
        platform = (
            "image"
            if body.image_id
            else (platform_for(body.source_url) if body.source_url else "supplied_text")
        )
        source = None
        if body.ai_account == "chatgpt":
            personal = chatgpt.connection(s["id"], str(body.chatgpt_connection_id))
            if not body.ai_destination or body.ai_destination[2] != personal["model"]:
                raise DomainError("chatgpt_configuration_changed", 409)
        if body.source_id:
            with database.connect() as db:
                source = db.execute(
                    "SELECT content_type FROM import_source WHERE id=?", (str(body.source_id),)
                ).fetchone()
            if source is None:
                raise DomainError("import_source_not_found", 404)
            platform = (
                "image"
                if source[0].startswith("image/")
                else ("pdf" if source[0] == "application/pdf" else "video")
            )
        try:
            selected_ai = load_configuration(data_dir / "config") if body.use_ai else None
        except DomainError:
            selected_ai = None  # Structured metadata does not need an AI configuration.
        with database.transaction() as db:
            previous = db.execute(
                "SELECT state,request_fingerprint FROM import_draft WHERE id=?", (iid,)
            ).fetchone()
            if previous and previous["request_fingerprint"] is not None:
                owner = db.execute(
                    "SELECT session_id FROM chatgpt_import WHERE import_id=?", (iid,)
                ).fetchone()
                if owner and owner["session_id"] != s["id"]:
                    raise DomainError("chatgpt_import_owner_mismatch", 403)
                if previous["request_fingerprint"] != import_fingerprint(
                    body.model_dump(mode="json")
                ):
                    raise DomainError("idempotency_conflict", 409)
                return {"id": iid, "state": previous["state"]}
            if previous:
                job = db.execute(
                    "SELECT payload FROM background_job WHERE dedupe_key=?", ("import:" + iid,)
                ).fetchone()
                old = json.loads(job[0]) if job else {}
                if any(
                    old.get(key) != value
                    for key, value in {
                        "text": body.text,
                        "source_url": body.source_url,
                        "use_ai": body.use_ai,
                        "consent_external_ai": body.consent_external_ai,
                        "image_id": str(body.image_id) if body.image_id else None,
                        "source_id": str(body.source_id) if body.source_id else None,
                        "ai_destination": list(body.ai_destination)
                        if body.ai_destination
                        else None,
                    }.items()
                ):
                    raise DomainError("idempotency_conflict", 409)
                return {"id": iid, "state": previous[0]}
            if not rate_limit(db, "imports", maximum=20, seconds=3600):
                raise DomainError("import_rate_limited", 429)
            if (
                body.image_id
                and not db.execute(
                    "SELECT 1 FROM recipe_media WHERE id=?", (str(body.image_id),)
                ).fetchone()
            ):
                raise DomainError("image_not_found", 404)
            db.execute(
                "INSERT INTO import_draft(id,source_url,source_platform,state,recipe,warnings,error_code,confirmed_recipe_id,created_at,request_fingerprint,source_id) VALUES (?,?,?,'queued',NULL,'[]',NULL,NULL,?,?,?)",
                (
                    iid,
                    body.source_url,
                    platform,
                    time.time(),
                    import_fingerprint(body.model_dump(mode="json")),
                    str(body.source_id) if body.source_id else None,
                ),
            )
            enqueue(
                db,
                "recipe.import",
                "import:" + iid,
                {
                    "id": iid,
                    **(
                        {"ai_account": "chatgpt", "consent_chatgpt_background": True}
                        if body.ai_account == "chatgpt"
                        else {}
                    ),
                    "text": body.text,
                    "source_url": body.source_url,
                    "use_ai": body.use_ai,
                    "consent_external_ai": body.consent_external_ai,
                    "image_id": str(body.image_id) if body.image_id else None,
                    "source_id": str(body.source_id) if body.source_id else None,
                    "ai_destination": list(body.ai_destination)
                    if body.ai_destination
                    else [
                        selected_ai.provider,
                        selected_ai.base_url,
                        selected_ai.model,
                    ]
                    if selected_ai
                    else [],
                },
            )
            if body.ai_account == "chatgpt":
                db.execute(
                    "INSERT INTO chatgpt_import VALUES (?,?,?)",
                    (iid, s["id"], str(body.chatgpt_connection_id)),
                )
        return {"id": iid, "state": "queued"}

    @app.get("/api/v1/imports/{import_id}", response_model=RecipeImportStatus)
    def get_import(import_id: UUID, s=Depends(session)):
        with database.connect() as db:
            row = db.execute("SELECT * FROM import_draft WHERE id=?", (str(import_id),)).fetchone()
            photo = db.execute(
                "SELECT image_id,source_url FROM import_source_photo WHERE import_id=?",
                (str(import_id),),
            ).fetchone()
        if not row:
            raise DomainError("not_found", 404)
        return {
            **{
                key: row[key]
                for key in row.keys()
                if key not in ("request_fingerprint", "finished_at", "source_id", "extraction")
            },
            "recipe": json.loads(row["recipe"]) if row["recipe"] else None,
            "warnings": json.loads(row["warnings"]),
            "extraction": json.loads(row["extraction"]) if row["extraction"] else None,
            "source_photo": dict(photo) if photo else None,
        }

    @app.delete("/api/v1/imports/{import_id}", status_code=204)
    def cancel_import(import_id: UUID, s=Depends(session)):
        with database.transaction() as db:
            db.execute(
                "UPDATE import_draft SET state='cancelled',finished_at=COALESCE(finished_at,?) WHERE id=? AND state!='confirmed'",
                (time.time(), str(import_id)),
            )

    @app.post("/api/v1/imports/{import_id}/confirm", response_model=MutationResult)
    def confirm_import(
        import_id: UUID,
        body: Mutation,
        x_mealf_sync_cursor: int | None = Header(default=None, ge=0),
        x_mealf_sync_token: str | None = Header(default=None, pattern=r"^(root|[a-f0-9]{32})$"),
        legacy_cursor: int | None = Header(
            default=None, alias=HEADER_PREFIX + "-sync-cursor", include_in_schema=False, ge=0
        ),
        legacy_token: str | None = Header(
            default=None,
            alias=HEADER_PREFIX + "-sync-token",
            include_in_schema=False,
            pattern=r"^(root|[a-f0-9]{32})$",
        ),
        s=Depends(session),
    ):
        if legacy_cursor is not None or legacy_token is not None:
            if x_mealf_sync_cursor is not None or x_mealf_sync_token is not None:
                if (legacy_cursor, legacy_token) != (x_mealf_sync_cursor, x_mealf_sync_token):
                    raise DomainError("sync_checkpoint_conflict", 422)
            else:
                x_mealf_sync_cursor, x_mealf_sync_token = legacy_cursor, legacy_token
        if body.kind != "recipe" or body.operation != "upsert":
            raise DomainError("recipe_mutation_required")
        with database.transaction() as db:
            if (x_mealf_sync_cursor is None) != (x_mealf_sync_token is None):
                raise DomainError("sync_checkpoint_required", 422)
            if x_mealf_sync_cursor is not None and x_mealf_sync_token is not None:
                validate_anchor(
                    db, SyncAnchor(cursor=x_mealf_sync_cursor, token=x_mealf_sync_token)
                )
            row = db.execute("SELECT * FROM import_draft WHERE id=?", (str(import_id),)).fetchone()
            if not row or row["state"] not in ("preview", "confirmed"):
                raise DomainError("import_not_ready", 409)
            if row["confirmed_recipe_id"] and row["confirmed_recipe_id"] != str(body.entity_id):
                raise DomainError("import_already_confirmed", 409)
            if (
                not body.payload
                or not getattr(body.payload, "ingredients", None)
                or not getattr(body.payload, "steps", None)
            ):
                raise DomainError("import_incomplete_review_required", 422)
            result = apply_mutation(db, body, s["device_id"])
            db.execute(
                "UPDATE import_draft SET state='confirmed',confirmed_recipe_id=?,finished_at=COALESCE(finished_at,?) WHERE id=?",
                (str(body.entity_id), time.time(), str(import_id)),
            )
        return result

    @app.get("/api/v1/household/status")
    def household_status(s=Depends(session)):
        with database.connect() as db:
            return {
                "recipes": db.execute(
                    "SELECT COUNT(*) FROM entity WHERE kind='recipe' AND deleted=0"
                ).fetchone()[0],
                "pending_jobs": db.execute(
                    "SELECT COUNT(*) FROM background_job WHERE state IN ('queued','running')"
                ).fetchone()[0],
            }

    @app.get("/api/v1/admin/status", response_model=AdministrationStatus)
    def administration_status(s=Depends(session)):
        with database.connect() as db:
            media = db.execute("SELECT COALESCE(SUM(byte_count),0) FROM recipe_media").fetchone()[0]
            jobs = db.execute(
                "SELECT COUNT(*) FROM background_job WHERE state IN ('queued','running')"
            ).fetchone()[0]
            recipes = db.execute(
                "SELECT COUNT(*) FROM entity WHERE kind='recipe' AND deleted=0"
            ).fetchone()[0]
        size = 0
        for path in (
            database.path,
            Path(str(database.path) + "-wal"),
            Path(str(database.path) + "-shm"),
        ):
            try:
                size += path.stat().st_size
            except FileNotFoundError:
                pass
        return AdministrationStatus(
            database_bytes=size,
            media_bytes=media,
            disk_free_bytes=shutil.disk_usage(data_dir).free,
            pending_jobs=jobs,
            recipes=recipes,
        )

    @app.get("/api/v1/admin/jobs", response_model=list[JobInfo])
    def jobs(
        limit: int = Query(default=100, ge=1, le=100),
        state: Literal["queued", "running", "done", "failed"] | None = None,
        s=Depends(session),
    ):
        with database.connect() as db:
            return recent_jobs(db, limit, state)

    @app.get("/api/v1/admin/diagnostics", response_model=AdministrationDiagnostics)
    def administration_diagnostics(
        limit: int = Query(default=20, ge=1, le=100), s=Depends(session)
    ):
        return diagnostics(database, limit)

    @app.get("/admin", include_in_schema=False)
    def admin_redirect():
        from fastapi.responses import RedirectResponse

        return RedirectResponse("/admin/", status_code=307)

    @app.get("/admin/", response_class=HTMLResponse, include_in_schema=False)
    def web_console():
        return (Path(__file__).parent / "web" / "index.html").read_text()

    @app.get("/admin/console.js", include_in_schema=False)
    def console_script():
        from fastapi.responses import FileResponse

        return FileResponse(
            Path(__file__).parent / "web" / "console.js", media_type="text/javascript"
        )

    @app.get("/admin/console.css", include_in_schema=False)
    def console_style():
        from fastapi.responses import FileResponse

        return FileResponse(Path(__file__).parent / "web" / "console.css", media_type="text/css")

    @app.post("/api/v1/admin/login")
    def browser_login(body: Credentials, request: Request):
        expected = os.environ.get("BASE_URL", "https://localhost").rstrip("/")
        if request.headers.get("origin") != expected:
            raise DomainError("origin_forbidden", 403)
        tokens = login(body, request, admin_only=True)
        response = JSONResponse({"authenticated": True, "expires_in": 900})
        response.set_cookie(
            "mealf_session",
            tokens.access_token,
            secure=True,
            httponly=True,
            samesite="strict",
            max_age=900,
            path="/api/v1",
        )
        response.set_cookie(
            "mealf_csrf",
            secrets.token_urlsafe(32),
            secure=True,
            httponly=False,
            samesite="strict",
            max_age=900,
            path="/",
        )
        response.delete_cookie(PREFIX + "_session", path="/")
        response.delete_cookie(PREFIX + "_csrf", path="/")
        return response

    @app.post("/api/v1/admin/logout", status_code=204)
    def browser_logout(s=Depends(session)):
        logout(s)
        from fastapi import Response

        response = Response(status_code=204)
        response.delete_cookie("mealf_session", path="/api/v1")
        response.delete_cookie("mealf_session", path="/")
        response.delete_cookie(PREFIX + "_session", path="/")
        response.delete_cookie(PREFIX + "_csrf", path="/")
        response.delete_cookie("mealf_csrf", path="/")
        return response

    @app.put("/api/v1/media/{image_id}", response_model=MediaInfo)
    async def upload_photo(image_id: UUID, file: UploadFile = File(...), s=Depends(session)):
        try:
            raw = await file.read(MAX_UPLOAD_BYTES + 1)
            return await durable_work(put_media, database, image_id, raw, file.content_type or "")
        finally:
            await file.close()

    @app.get("/api/v1/media/{image_id}/info", response_model=MediaInfo)
    def photo_info(image_id: UUID, s=Depends(session)):
        with database.connect() as db:
            row = db.execute("SELECT * FROM recipe_media WHERE id=?", (str(image_id),)).fetchone()
        if not row:
            raise DomainError("image_not_found", 404)
        return info_for(row)

    @app.get(
        "/api/v1/media/{image_id}",
        response_class=Response,
        responses={
            200: {"content": {"image/jpeg": {"schema": {"type": "string", "format": "binary"}}}}
        },
    )
    def download_photo(image_id: UUID, s=Depends(session)):
        with database.connect() as db:
            row = db.execute(
                "SELECT data,sha256 FROM recipe_media WHERE id=?", (str(image_id),)
            ).fetchone()
        if not row:
            raise DomainError("image_not_found", 404)
        return Response(
            row["data"], media_type="image/jpeg", headers={"ETag": '"' + row["sha256"] + '"'}
        )

    @app.get(
        "/api/v1/admin/export/archive",
        response_class=FileResponse,
        responses={
            200: {
                "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}}
            }
        },
    )
    async def download_archive(s=Depends(session)):
        async with archive_slots:
            path = await durable_work(export_archive, database)
        return FileResponse(
            path,
            media_type="application/zip",
            filename="mealf-household.zip",
            background=BackgroundTask(path.unlink, missing_ok=True),
        )

    @app.post(
        "/api/v1/admin/import/archive",
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}},
            }
        },
    )
    async def restore_archive(request: Request, s=Depends(session)):
        if request.headers.get("content-type", "").split(";")[0] != "application/zip":
            raise DomainError("archive_content_type_required", 415)
        # Stream authenticated uploads to a protected file rather than buffering a whole
        # household image library in memory. The import worker never extracts member paths.
        path = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix=".restore-", suffix=".zip", dir=data_dir / "jobs", delete=False
            ) as output:
                path = Path(output.name)
                count = 0
                async for chunk in request.stream():
                    count += len(chunk)
                    if count > MAX_ARCHIVE:
                        raise DomainError("archive_size_limit", 413)
                    await durable_work(output.write, chunk)
            return await durable_work(import_archive, database, path, s["device_id"])
        finally:
            if path:
                path.unlink(missing_ok=True)

    @app.get("/api/v1/admin/export", response_model=HouseholdExport)
    def export_data(s=Depends(session)):
        return export_household(database)

    @app.post("/api/v1/admin/import")
    def import_data(body: HouseholdExport, s=Depends(session)):
        return import_household(database, body, s["device_id"])

    @app.get("/api/v1/household")
    def household_settings(s=Depends(session)):
        with database.connect() as db:
            return dict(db.execute("SELECT name,timezone,language FROM household").fetchone())

    @app.put("/api/v1/household", response_model=HouseholdSettings)
    def update_household(body: HouseholdSettings, s=Depends(session)):
        with database.transaction() as db:
            db.execute(
                "UPDATE household SET name=?,timezone=?,language=? WHERE id=1",
                (body.name, body.timezone, body.language),
            )
            enqueue(db, "shopping.reconcile", "shopping.current", {})
        return body

    @app.post("/api/v1/auth/password", status_code=204)
    def change_password(body: PasswordChange, s=Depends(session)):
        with database.transaction() as db:
            allowed = rate_limit(db, "password-change:" + s["id"], maximum=5)
        if not allowed:
            raise DomainError("rate_limited", 429)
        with database.transaction() as db:
            h = db.execute(
                "SELECT password_hash FROM household_user WHERE id=?", (s["user_id"],)
            ).fetchone()
            if not verify_password(body.current_password, h[0]):
                raise DomainError("invalid_credentials", 401)
            db.execute(
                "UPDATE household_user SET password_hash=? WHERE id=?",
                (hasher.hash(body.new_password), s["user_id"]),
            )
            db.execute("UPDATE session SET revoked=1 WHERE user_id=?", (s["user_id"],))
            db.execute(
                "INSERT INTO audit_event(code,created_at) VALUES (?,?)",
                ("password_changed", time.time()),
            )

    register_pwa_auth(app, database, login, setup)
    from fastapi.staticfiles import StaticFiles

    packaged_pwa = Path(__file__).parent / "web" / "pwa"
    development_pwa = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    pwa = packaged_pwa if packaged_pwa.is_dir() else development_pwa
    if (pwa / "index.html").is_file():
        app.mount("/app", StaticFiles(directory=pwa, html=True), name="pwa")
    return app
