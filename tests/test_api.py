from uuid import uuid4

from fastapi.testclient import TestClient

from aircooker.app import create_app


def test_bootstrap_locked_and_auth_required(harness, tmp_path):
    c, app, device, tokens = harness
    assert not (tmp_path / "config" / "setup-token").exists()
    assert c.get("/api/v1/system/info").json()["configured"]
    assert c.get("/api/v1/recipes", headers={"Authorization": ""}).status_code == 401
    body = {
        "name": "Second",
        "username": "x",
        "password": "another long password",
        "device_id": device,
    }
    assert c.post("/api/v1/setup", json=body).status_code == 409
    assert app.state.database.path.exists()


def test_wrong_setup_token_and_no_password_echo(tmp_path):
    app = create_app(tmp_path, False)
    with TestClient(app) as c:
        body = {
            "name": "Home",
            "username": "cook",
            "password": "valid long secret",
            "device_id": str(uuid4()),
        }
        assert c.post("/api/v1/setup", json=body).status_code == 403
        body["password"] = "short"
        response = c.post("/api/v1/setup", json=body)
        assert response.status_code == 422
        assert "short" not in response.text


def test_rotation_replay_revokes_session(harness):
    c, app, device, tokens = harness
    new = c.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert new.status_code == 200
    assert c.get("/api/v1/recipes").status_code == 401
    fresh = new.json()
    c.headers["Authorization"] = "Bearer " + fresh["access_token"]
    assert c.get("/api/v1/recipes").status_code == 200
    assert (
        c.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code
        == 401
    )
    assert c.get("/api/v1/recipes").status_code == 401


def test_login_rate_limit_persists_failures(harness):
    c, app, device, tokens = harness
    for _ in range(10):
        assert (
            c.post(
                "/api/v1/auth/login",
                json={"username": "cook", "password": "incorrect", "device_id": device},
            ).status_code
            == 401
        )
    assert (
        c.post(
            "/api/v1/auth/login",
            json={"username": "cook", "password": "incorrect", "device_id": device},
        ).status_code
        == 429
    )


def test_sessions_revoked_independently(harness):
    c, app, device, tokens = harness
    second = c.post(
        "/api/v1/auth/login",
        json={"username": "cook", "password": "a strong test password", "device_id": str(uuid4())},
    ).json()
    assert c.delete("/api/v1/auth/sessions/" + second["session_id"]).status_code == 204
    assert c.get("/api/v1/recipes").status_code == 200
    assert (
        c.get(
            "/api/v1/recipes", headers={"Authorization": "Bearer " + second["access_token"]}
        ).status_code
        == 401
    )


def test_contract_generated(harness):
    c, *_ = harness
    contract = c.get("/api/v1/openapi.json").json()
    assert contract["info"]["version"] == "0.1.0"
    assert "/api/v1/sync/push" in contract["paths"]
    assert "Mutation" in contract["components"]["schemas"]


def test_password_change_revokes_all_sessions(harness):
    c, app, device, tokens = harness
    assert (
        c.post(
            "/api/v1/auth/password",
            json={"current_password": "wrong", "new_password": "another long password"},
        ).status_code
        == 401
    )
    assert (
        c.post(
            "/api/v1/auth/password",
            json={
                "current_password": "a strong test password",
                "new_password": "another long password",
            },
        ).status_code
        == 204
    )
    assert c.get("/api/v1/recipes").status_code == 401
    assert (
        c.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code
        == 401
    )
    assert (
        c.post(
            "/api/v1/auth/login",
            json={"username": "cook", "password": "another long password", "device_id": device},
        ).status_code
        == 200
    )


def test_household_timezone_validation(harness):
    c, app, device, tokens = harness
    assert (
        c.put(
            "/api/v1/household",
            json={"name": "Home", "timezone": "imaginary/zone", "language": "de"},
        ).status_code
        == 422
    )
    assert (
        c.put(
            "/api/v1/household",
            json={"name": "Home", "timezone": "Europe/Berlin", "language": "de"},
        ).status_code
        == 200
    )
    assert c.get("/api/v1/household").json()["timezone"] == "Europe/Berlin"
