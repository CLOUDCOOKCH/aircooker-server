from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from aircooker.app import create_app
from aircooker.pwa_auth import ACCESS_COOKIE, AUTH_PATH, CSRF_COOKIE, REFRESH_COOKIE


@pytest.fixture
def browser(harness, monkeypatch):
    _, app, *_ = harness
    monkeypatch.setenv("BASE_URL", "https://localhost")
    with TestClient(app, base_url="https://localhost") as client:
        client.headers.update({"Origin": "https://localhost", "X-Aircooker-Client": "pwa"})
        yield client, app


def sign_in(client):
    return client.post(
        AUTH_PATH + "/login",
        json={"username": "cook", "password": "a strong test password", "device_id": str(uuid4())},
    )


def csrf(client):
    return {"X-CSRF-Token": client.cookies.get(CSRF_COOKIE, "")}


def test_pwa_cookie_credentials_are_http_only_and_never_in_json(browser):
    client, _ = browser
    response = sign_in(client)
    assert response.status_code == 200
    assert set(response.json()) == {"authenticated", "session_id", "device_id", "expires_in"}
    for cookie in response.headers.get_list("set-cookie"):
        assert "Secure" in cookie and "SameSite=strict" in cookie
        if cookie.startswith((ACCESS_COOKIE, REFRESH_COOKIE)):
            assert "HttpOnly" in cookie
    assert client.get("/api/v1/recipes").status_code == 200
    assert client.get(AUTH_PATH + "/session").json()["session_id"] == response.json()["session_id"]
    assert "no-store" in response.headers["cache-control"]
    # The console has a separate cookie; logging into the PWA does not grant its session.
    assert (
        client.get("/api/v1/admin/status", headers={"X-Aircooker-Client": "console"}).status_code
        == 401
    )


def test_pwa_requires_origin_and_csrf_on_mutations(browser):
    client, _ = browser
    assert (
        client.post(
            AUTH_PATH + "/login",
            headers={"Origin": "https://other.invalid"},
            json={
                "username": "cook",
                "password": "a strong test password",
                "device_id": str(uuid4()),
            },
        ).status_code
        == 403
    )
    assert sign_in(client).status_code == 200
    for route in (AUTH_PATH + "/refresh", AUTH_PATH + "/logout"):
        assert client.post(route).status_code == 403
        assert (
            client.post(
                route, headers={**csrf(client), "Origin": "https://other.invalid"}
            ).status_code
            == 403
        )
    assert client.post("/api/v1/integrations/bring/reconcile").status_code == 403
    assert (
        client.post("/api/v1/integrations/bring/reconcile", headers=csrf(client)).status_code == 202
    )


def test_pwa_rotates_after_access_expiry_and_replay_revokes_only_its_session(browser, harness):
    client, app = browser
    response = sign_in(client)
    session_id = response.json()["session_id"]
    original = client.cookies.get(REFRESH_COOKIE)
    with app.state.database.transaction() as db:
        db.execute("UPDATE session SET access_expires=0 WHERE id=?", (session_id,))
    assert client.get("/api/v1/recipes").status_code == 401
    refreshed = client.post(AUTH_PATH + "/refresh", headers=csrf(client))
    assert refreshed.status_code == 200
    assert refreshed.json()["session_id"] == session_id
    assert original != client.cookies.get(REFRESH_COOKIE)
    assert client.get("/api/v1/recipes").status_code == 200
    client.cookies.set(REFRESH_COOKIE, original, domain="localhost.local", path=AUTH_PATH)
    rejected = client.post(AUTH_PATH + "/refresh", headers=csrf(client))
    assert rejected.status_code == 401
    assert ACCESS_COOKIE not in client.cookies and REFRESH_COOKIE not in client.cookies
    assert client.get("/api/v1/recipes").status_code == 401
    assert harness[0].get("/api/v1/recipes").status_code == 200


@pytest.mark.parametrize("missing_refresh", [False, True])
def test_pwa_logout_revokes_when_access_expired_or_refresh_cookie_missing(browser, missing_refresh):
    client, app = browser
    sid = sign_in(client).json()["session_id"]
    if missing_refresh:
        client.cookies.delete(REFRESH_COOKIE, domain="localhost.local", path=AUTH_PATH)
    else:
        with app.state.database.transaction() as db:
            db.execute("UPDATE session SET access_expires=0 WHERE id=?", (sid,))
    assert client.post(AUTH_PATH + "/logout", headers=csrf(client)).status_code == 204
    assert ACCESS_COOKIE not in client.cookies and REFRESH_COOKIE not in client.cookies
    assert CSRF_COOKIE not in client.cookies
    with app.state.database.connect() as db:
        assert db.execute("SELECT revoked FROM session WHERE id=?", (sid,)).fetchone()[0] == 1


def test_pwa_setup_requires_local_token_and_cannot_reopen_bootstrap(tmp_path, monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://localhost")
    app = create_app(tmp_path, False)
    token = (tmp_path / "config/setup-token").read_text()
    body = {
        "name": "Home",
        "username": "Bäcker",
        "password": "a long test password",
        "device_id": str(uuid4()),
    }
    with TestClient(
        app,
        base_url="https://localhost",
        headers={"Origin": "https://localhost", "X-Aircooker-Client": "pwa"},
    ) as client:
        assert client.post(AUTH_PATH + "/setup", json=body).status_code == 403
        result = client.post(AUTH_PATH + "/setup", json=body, headers={"X-Setup-Token": token})
        assert result.status_code == 201 and "refresh_token" not in result.json()
        assert client.get("/api/v1/recipes").status_code == 200
        assert (
            client.post(
                AUTH_PATH + "/setup", json=body, headers={"X-Setup-Token": token}
            ).status_code
            == 409
        )
        assert (
            client.post(
                AUTH_PATH + "/login",
                json={k: body[k] for k in ("username", "password", "device_id")},
            ).status_code
            == 200
        )
