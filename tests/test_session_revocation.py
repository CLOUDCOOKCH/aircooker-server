from uuid import uuid4

import pytest


def test_revoke_rotated_capability_is_idempotent_and_device_scoped(harness):
    c, app, device, original = harness
    other = c.post(
        "/api/v1/auth/login",
        json={"username": "cook", "password": "a strong test password", "device_id": str(uuid4())},
    ).json()
    rotated = c.post(
        "/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]}
    ).json()
    # The original secret remains sufficient if logout raced a lost refresh response.
    c.headers.clear()
    for _ in range(2):
        response = c.post("/api/v1/auth/revoke", json={"refresh_token": original["refresh_token"]})
        assert response.status_code == 204
        assert not response.content
    assert (
        c.get(
            "/api/v1/recipes", headers={"Authorization": "Bearer " + rotated["access_token"]}
        ).status_code
        == 401
    )
    assert (
        c.post("/api/v1/auth/refresh", json={"refresh_token": rotated["refresh_token"]}).status_code
        == 401
    )
    assert (
        c.get(
            "/api/v1/recipes", headers={"Authorization": "Bearer " + other["access_token"]}
        ).status_code
        == 200
    )


@pytest.mark.parametrize("expired", [False, True])
def test_revoke_current_expired_and_unknown_secrets(harness, expired):
    c, app, device, tokens = harness
    if expired:
        with app.state.database.transaction() as db:
            db.execute("UPDATE session SET access_expires=0,refresh_expires=0")
    c.headers.clear()
    for token in ["x" * 64, tokens["refresh_token"], tokens["refresh_token"]]:
        response = c.post("/api/v1/auth/revoke", json={"refresh_token": token})
        assert response.status_code == 204
        assert not response.content
    with app.state.database.connect() as db:
        assert db.execute("SELECT revoked FROM session").fetchone()[0] == 1


def test_revoke_validation_and_rate_limit_do_not_leak_tokens(harness):
    c, app, device, tokens = harness
    c.headers.clear()
    assert (
        c.post("/api/v1/auth/revoke", json={"session_id": tokens["session_id"]}).status_code == 422
    )
    secret = "too-short-secret"
    response = c.post("/api/v1/auth/revoke", json={"refresh_token": secret})
    assert response.status_code == 422 and secret not in response.text
    for _ in range(60):
        assert c.post("/api/v1/auth/revoke", json={"refresh_token": "x" * 64}).status_code == 204
    assert (
        c.post("/api/v1/auth/revoke", json={"refresh_token": tokens["refresh_token"]}).status_code
        == 429
    )
    assert (
        c.get(
            "/api/v1/recipes", headers={"Authorization": "Bearer " + tokens["access_token"]}
        ).status_code
        == 200
    )
