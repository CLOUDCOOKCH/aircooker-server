"""Compatibility fixtures mirror durable identifiers from the published previews."""

import io
import json
import os
import sqlite3
import zipfile

import pytest
from fastapi.testclient import TestClient

from mealf.app import create_app
from mealf.db import Database
from mealf.legacy import ARCHIVE_FORMAT, DATABASE_NAME, EXPORT_FORMAT, migrate_database
from mealf.pwa_auth import ACCESS_COOKIE, AUTH_PATH, CSRF_COOKIE, REFRESH_COOKIE
from tests.test_media import clean_client, save_recipe, upload
from tests.test_pwa_auth import sign_in


def test_legacy_admin_session_keeps_csrf_protection_and_can_sign_out(harness, monkeypatch):
    _, app, device, _ = harness
    monkeypatch.setenv("BASE_URL", "https://localhost")
    with TestClient(
        app, base_url="https://localhost", headers={"Origin": "https://localhost"}
    ) as client:
        response = client.post(
            "/api/v1/admin/login",
            json={
                "username": "cook",
                "password": "a strong test password",
                "device_id": device,
            },
        )
        assert response.status_code == 200
        session = client.cookies.get("mealf_session")
        csrf = client.cookies.get("mealf_csrf")
        client.cookies.clear()
        client.cookies.set("aircooker_session", session, domain="localhost.local", path="/")
        client.cookies.set("aircooker_csrf", csrf, domain="localhost.local", path="/")
        assert client.get("/api/v1/admin/status").status_code == 200
        assert client.post("/api/v1/admin/logout").status_code == 403
        assert (
            client.post("/api/v1/admin/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
        )
        assert not list(client.cookies.jar)
        client.cookies.set("aircooker_session", session, domain="localhost.local", path="/")
        assert client.get("/api/v1/admin/status").status_code == 401


def test_admin_namespace_leaves_root_for_the_landing_page(harness):
    client, *_ = harness
    redirect = client.get("/admin", follow_redirects=False)
    assert redirect.status_code == 307 and redirect.headers["location"] == "/admin/"
    console = client.get("/admin/")
    assert console.status_code == 200
    assert "/admin/console.css" in console.text and "/admin/console.js" in console.text
    assert "/app/brand/wordmark-v1.png" in console.text
    assert "aircooker" not in console.text.lower()
    for path in ("/admin/console.css", "/admin/console.js"):
        assert client.get(path).status_code == 200
    for path in ("/", "/console.css", "/console.js", "/admin/not-a-page"):
        assert client.get(path).status_code == 404
    assert client.get("/api/v1/system/info").status_code == 200


def test_database_rename_preserves_wal_data_and_resumes_after_link_publication(tmp_path):
    directory = tmp_path / "database"
    directory.mkdir()
    old = directory / DATABASE_NAME
    connection = sqlite3.connect(old, isolation_level=None)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("CREATE TABLE saved(value TEXT)")
    connection.execute("INSERT INTO saved VALUES ('offline receipt preserved')")
    # Keep the writer open: this row exists in the WAL, not just the main file.
    assert (directory / (DATABASE_NAME + "-wal")).stat().st_size > 0
    migrate_database(directory)
    connection.close()
    assert not old.exists()
    with sqlite3.connect(directory / "mealf.sqlite3") as check:
        assert check.execute("SELECT value FROM saved").fetchone()[0] == "offline receipt preserved"
    os.link(directory / "mealf.sqlite3", old)
    migrate_database(directory)
    assert not old.exists() and (directory / "mealf.sqlite3").exists()


def test_database_rename_refuses_ambiguous_households_and_uncheckpointed_wal(tmp_path):
    old = tmp_path / DATABASE_NAME
    current = tmp_path / "mealf.sqlite3"
    old.write_bytes(b"original household")
    current.write_bytes(b"another household")
    with pytest.raises(RuntimeError, match="Two different"):
        migrate_database(tmp_path)
    assert old.read_bytes() == b"original household"
    assert current.read_bytes() == b"another household"
    old.unlink()
    current.unlink()
    writer = sqlite3.connect(old, isolation_level=None)
    reader = sqlite3.connect(old, isolation_level=None)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("CREATE TABLE saved(value TEXT)")
        reader.execute("BEGIN")
        reader.execute("SELECT * FROM saved").fetchall()
        writer.execute("INSERT INTO saved VALUES ('must not be dropped')")
        with pytest.raises(RuntimeError, match="Stop every database"):
            migrate_database(tmp_path)
        assert old.exists() and not current.exists()
    finally:
        reader.close()
        writer.close()
    migrate_database(tmp_path)
    with sqlite3.connect(current) as check:
        assert check.execute("SELECT value FROM saved").fetchone()[0] == "must not be dropped"


def test_real_household_database_and_operator_entrypoint_survive_rename(tmp_path, mutation):
    from aircooker.app import create_app as deprecated_entrypoint

    assert deprecated_entrypoint is create_app
    root = tmp_path / "old-volume"
    with clean_client(root) as (client, app, device):
        identity = client.get("/api/v1/system/info").json()["instance_id"]
        save_recipe(client, mutation, device)
        access = client.headers["Authorization"]
        with app.state.database.connect() as db:
            migrations = db.execute("SELECT * FROM schema_migration ORDER BY version").fetchall()
    (root / "database/mealf.sqlite3").rename(root / "database" / DATABASE_NAME)
    upgraded = deprecated_entrypoint(root, run_worker=False)
    with TestClient(upgraded) as client:
        client.headers["Authorization"] = access
        assert client.get("/api/v1/system/info").json()["instance_id"] == identity
        assert (
            client.get("/api/v1/recipes").json()["items"][0]["payload"]["title"] == "Photo recipe"
        )
        with upgraded.state.database.connect() as db:
            assert (
                db.execute("SELECT * FROM schema_migration ORDER BY version").fetchall()
                == migrations
            )
        assert Database(root).path.name == "mealf.sqlite3"
        assert not (root / "database" / DATABASE_NAME).exists()


@pytest.mark.parametrize("archive", [False, True])
def test_legacy_export_formats_restore_recipes_and_media(harness, mutation, tmp_path, archive):
    client, _, device, _ = harness
    photo = upload(client).json()["id"]
    recipe, _ = save_recipe(client, mutation, device, photo)
    if archive:
        exported = client.get("/api/v1/admin/export/archive")
        assert "mealf" in exported.headers["content-disposition"]
        output = io.BytesIO()
        with (
            zipfile.ZipFile(io.BytesIO(exported.content)) as source,
            zipfile.ZipFile(output, "w") as target,
        ):
            manifest = json.loads(source.read("manifest.json"))
            assert manifest["format"] == "mealf-household-archive"
            assert manifest["household"]["format"] == "mealf-household"
            manifest["format"] = ARCHIVE_FORMAT
            manifest["household"]["format"] = EXPORT_FORMAT
            for name in source.namelist():
                target.writestr(
                    name, json.dumps(manifest) if name == "manifest.json" else source.read(name)
                )
    else:
        body = client.get("/api/v1/admin/export").json()
        assert body["format"] == "mealf-household"
        body["format"] = EXPORT_FORMAT
    with clean_client(tmp_path / "restored") as (target, _, _):
        response = (
            target.post(
                "/api/v1/admin/import/archive",
                content=output.getvalue(),
                headers={"Content-Type": "application/zip"},
            )
            if archive
            else target.post("/api/v1/admin/import", json=body)
        )
        assert response.status_code == 200, response.text
        assert target.get("/api/v1/recipes/" + recipe["entity_id"]).status_code == 200
        assert (
            target.get("/api/v1/media/" + photo).content
            == client.get("/api/v1/media/" + photo).content
        )


def test_legacy_browser_cookies_refresh_into_current_names_and_revoke_on_logout(
    harness, monkeypatch
):
    _, app, *_ = harness
    monkeypatch.setenv("BASE_URL", "https://localhost")
    with TestClient(app, base_url="https://localhost") as client:
        client.headers.update({"Origin": "https://localhost", "X-Aircooker-Client": "pwa"})
        sid = sign_in(client).json()["session_id"]
        for name, path in (
            (ACCESS_COOKIE, "/api/v1"),
            (REFRESH_COOKIE, AUTH_PATH),
            (CSRF_COOKIE, "/"),
        ):
            value = client.cookies.get(name)
            client.cookies.delete(name, domain="localhost.local", path=path)
            client.cookies.set(
                name.replace("mealf", "aircooker"), value, domain="localhost.local", path=path
            )
        legacy_csrf = client.cookies.get("aircooker_pwa_csrf")
        assert client.get("/api/v1/recipes").status_code == 200
        assert client.post(AUTH_PATH + "/refresh").status_code == 403
        refreshed = client.post(AUTH_PATH + "/refresh", headers={"X-CSRF-Token": legacy_csrf})
        assert refreshed.status_code == 200 and refreshed.json()["session_id"] == sid
        assert client.cookies.get(ACCESS_COOKIE) and client.cookies.get(REFRESH_COOKIE)
        assert not any(cookie.name.startswith("aircooker") for cookie in client.cookies.jar)
        response = client.post(
            AUTH_PATH + "/logout", headers={"X-CSRF-Token": client.cookies.get(CSRF_COOKIE)}
        )
        assert response.status_code == 204
        assert client.get("/api/v1/recipes").status_code == 401
        with app.state.database.connect() as db:
            assert db.execute("SELECT revoked FROM session WHERE id=?", (sid,)).fetchone()[0] == 1
