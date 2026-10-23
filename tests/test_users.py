from importlib.resources import files
from uuid import uuid4

from fastapi.testclient import TestClient

from mealf.app import create_app
from mealf.auth import digest, hasher
from mealf.db import Database

PASSWORD = "synthetic member password"
PATH = "/api/v1/admin/users"


def add(client, username="member", role="user"):
    response = client.post(PATH, json={"username": username, "password": PASSWORD, "role": role})
    assert response.status_code == 201, response.text
    assert set(response.json()) == {"id", "username", "role", "active"}
    return response.json()


def login(client, username="member", password=PASSWORD):
    device = str(uuid4())
    response = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password, "device_id": device}
    )
    assert response.status_code == 200, response.text
    return response.json(), {"Authorization": "Bearer " + response.json()["access_token"]}, device


def test_members_share_data_and_keep_identity_on_refresh(harness, mutation):
    client, _, _, _ = harness
    member = add(client)
    tokens, headers, device = login(client)
    assert client.get("/api/v1/auth/me", headers=headers).json() == member
    assert (
        client.post(
            "/api/v1/sync/push", json={"mutations": [mutation(device)]}, headers=headers
        ).status_code
        == 200
    )
    assert len(client.get("/api/v1/recipes").json()["items"]) == 1
    assert client.get("/api/v1/household", headers=headers).json()["name"] == "Test household"
    assert client.get("/api/v1/ai/status", headers=headers).status_code == 200
    assert client.get("/api/v1/household/status", headers=headers).json()["recipes"] == 1
    renewed = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    ).json()
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer " + renewed["access_token"]}
        ).json()
        == member
    )


def test_member_cannot_access_any_admin_route_or_configure_integrations(harness):
    client, app, *_ = harness
    member = add(client)
    _, headers, _ = login(client)
    # Exercise every registered admin operation, including malformed mutation bodies:
    # authorization must run before any protected work or transfer parsing.
    for route in app.routes:
        if (
            not getattr(route, "path", "").startswith("/api/v1/admin/")
            or route.path == "/api/v1/admin/login"
        ):
            continue
        path = route.path.replace("{user_id}", member["id"])
        for method in route.methods - {"HEAD", "OPTIONS"}:
            response = client.request(method, path, headers=headers)
            assert response.status_code == 403, (method, path, response.text)
            assert response.json()["error"]["code"] == "admin_required"
    for method, path, body in [
        ("PUT", "/api/v1/household", {"name": "Changed", "language": "en", "timezone": "UTC"}),
        (
            "POST",
            "/api/v1/integrations/bring/connect",
            {"email": "synthetic@example.test", "password": "synthetic"},
        ),
        ("GET", "/api/v1/integrations/bring/lists", None),
        ("PUT", "/api/v1/integrations/bring/configuration", {"list_id": str(uuid4())}),
        ("DELETE", "/api/v1/integrations/bring/disconnect", None),
        ("POST", "/api/v1/integrations/bring/verify", {}),
    ]:
        assert client.request(method, path, json=body, headers=headers).status_code == 403


def test_admin_cookie_login_denies_user_and_pwa_member_csrf(harness, monkeypatch):
    from mealf.pwa_auth import CSRF_COOKIE

    client, app, *_ = harness
    member = add(client)
    monkeypatch.setenv("BASE_URL", "https://localhost")
    with TestClient(
        app, base_url="https://localhost", headers={"Origin": "https://localhost"}
    ) as browser:
        body = {"username": "member", "password": PASSWORD, "device_id": str(uuid4())}
        response = browser.post("/api/v1/admin/login", json=body)
        assert response.status_code == 403 and not response.cookies
        assert browser.post("/api/v1/pwa/auth/login", json=body).status_code == 200
        headers = {"X-Mealf-Client": "pwa", "X-CSRF-Token": browser.cookies[CSRF_COOKIE]}
        assert browser.get("/api/v1/auth/me", headers=headers).json() == member
        assert browser.get(PATH, headers=headers).status_code == 403
        assert (
            browser.patch(
                PATH + "/" + member["id"], headers=headers, json={"role": "admin"}
            ).status_code
            == 403
        )


def test_role_password_and_disable_revoke_only_target_user(harness):
    client, _, _, admin_tokens = harness
    member = add(client)
    tokens, headers, _ = login(client)
    assert client.patch(PATH + "/" + member["id"], json={"role": "admin"}).status_code == 200
    assert client.get(PATH, headers=headers).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )
    _, headers, _ = login(client)
    assert client.get(PATH, headers=headers).status_code == 200
    assert (
        client.patch(
            PATH + "/" + member["id"], json={"role": "user", "password": "new synthetic password"}
        ).status_code
        == 200
    )
    assert client.get(PATH, headers=headers).status_code == 401
    tokens, headers, device = login(client, password="new synthetic password")
    assert client.patch(PATH + "/" + member["id"], json={"active": False}).status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": "member", "password": "new synthetic password", "device_id": device},
        ).status_code
        == 401
    )
    assert client.get(PATH).status_code == 200
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": admin_tokens["refresh_token"]}
        ).status_code
        == 200
    )


def test_last_admin_and_duplicate_or_invalid_accounts_are_atomic(harness):
    client, *_ = harness
    admin = client.get("/api/v1/auth/me").json()
    for patch in [{"role": "user"}, {"active": False}]:
        assert (
            client.patch(PATH + "/" + admin["id"], json=patch).json()["error"]["code"]
            == "last_admin_required"
        )
    add(client)
    assert client.post(PATH, json={"username": "member", "password": PASSWORD}).status_code == 409
    for body in [
        {"username": "", "password": PASSWORD},
        {"username": "other", "password": "short"},
        {"username": "other", "password": PASSWORD, "role": "owner"},
    ]:
        assert client.post(PATH, json=body).status_code == 422
    for patch in [
        {},
        {"role": None},
        {"active": None},
        {"password": "short"},
        {"username": "member"},
    ]:
        assert client.patch(PATH + "/" + admin["id"], json=patch).status_code in (409, 422)
    assert client.get("/api/v1/auth/me").json() == admin


def test_password_change_and_sessions_are_per_account(harness):
    client, *_ = harness
    member = add(client)
    _, headers, _ = login(client)
    sessions = client.get("/api/v1/auth/sessions", headers=headers).json()
    assert len(sessions) == 1
    admin_sessions = client.get("/api/v1/auth/sessions").json()
    admin_session = next(row for row in admin_sessions if row["current"])
    assert (
        client.delete("/api/v1/auth/sessions/" + admin_session["id"], headers=headers).status_code
        == 204
    )
    assert client.get(PATH).status_code == 200
    assert (
        client.post(
            "/api/v1/auth/password",
            headers=headers,
            json={
                "current_password": PASSWORD,
                "new_password": "changed synthetic member password",
            },
        ).status_code
        == 204
    )
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert client.get(PATH).status_code == 200
    _, headers, _ = login(client, password="changed synthetic member password")
    assert client.get("/api/v1/auth/me", headers=headers).json() == member


def test_released_upgrade_preserves_login_and_existing_session(tmp_path, monkeypatch):
    import time

    resources = tmp_path / "released"
    (resources / "migrations").mkdir(parents=True)
    for source in files("mealf").joinpath("migrations").iterdir():
        if source.name.endswith(".sql") and source.name < "017":
            (resources / "migrations" / source.name).write_text(source.read_text())
    root = tmp_path / "data"
    identity, device, sid = str(uuid4()), str(uuid4()), str(uuid4())
    with monkeypatch.context() as patch:
        patch.setattr("mealf.db.files", lambda package: resources)
        database = Database(root)
        with database.transaction() as db:
            db.execute(
                "INSERT INTO household VALUES (1,?,?,?,?,?,?)",
                ("Retained", "UTC", "en", "cook", hasher.hash(PASSWORD), identity),
            )
            db.execute("INSERT INTO device VALUES (?,?)", (device, time.time()))
            db.execute(
                "INSERT INTO session VALUES (?,?,?,?,?,?,0)",
                (
                    sid,
                    device,
                    digest("synthetic-access"),
                    digest("synthetic-refresh"),
                    time.time() + 900,
                    time.time() + 86400,
                ),
            )
    with TestClient(create_app(root, run_worker=False)) as client:
        client.headers["Authorization"] = "Bearer synthetic-access"
        assert client.get("/api/v1/auth/me").json() == {
            "id": identity,
            "username": "cook",
            "role": "admin",
            "active": True,
        }
        assert client.get(PATH).status_code == 200
        assert login(client, "cook")[0]["access_token"]
        Database(root)
        assert len(client.get(PATH).json()) == 1
