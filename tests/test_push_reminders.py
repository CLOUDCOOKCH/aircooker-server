import base64
import json
from datetime import UTC, date, datetime, timedelta
from email.utils import format_datetime
from uuid import uuid4

import http_ece
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from mealf.db import Database
from mealf.errors import DomainError
from mealf.jobs import claim, finish
from mealf.reminders import PushDeliveryError, Reminders, due_at
from mealf.webpush import PushResponse, encoded, retry_delay

PATH = "/api/v1/notifications/push"
NOW = datetime(2026, 10, 21, 16, 0, tzinfo=UTC)  # 18:00 in Europe/Zurich.


@pytest.fixture(autouse=True)
def public_push_origin(monkeypatch):
    monkeypatch.setenv("BASE_URL", "https://kitchen.example")


def registration():
    private = ec.generate_private_key(ec.SECP256R1())
    public = private.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    auth = b"synthetic-auth!!"
    assert len(auth) == 16
    return (
        {
            "endpoint": "https://web.push.apple.com/synthetic-" + str(uuid4()),
            "keys": {"p256dh": encoded(public), "auth": encoded(auth)},
            "language": "en",
        },
        private,
        auth,
    )


def schedule(harness, mutation):
    client, app, device, _ = harness
    body, _, _ = registration()
    response = client.put(PATH + "/subscription", json=body)
    assert response.status_code == 200, response.text
    recipe = mutation(device)
    meal = mutation(
        device,
        kind="meal",
        payload={
            "recipe_id": recipe["entity_id"],
            "date": "2026-10-21",
            "category": "dinner",
            "servings": "2",
        },
    )
    for request in (recipe, meal):
        result = client.post("/api/v1/sync/push", json={"mutations": [request]})
        assert result.status_code == 200, result.text
    with app.state.database.transaction() as db:
        db.execute("UPDATE background_job SET state='done'")
    app.state.reminders.enqueue_due(NOW)
    job = claim(app.state.database)
    assert job and job["kind"] == "notification.meal"
    return app.state.reminders, job, meal


def test_subscriptions_are_encrypted_device_scoped_and_vapid_survives_restart(harness):
    client, app, device, _ = harness
    body, _, _ = registration()
    before = client.get(PATH).json()
    assert before["subscribed"] is False
    response = client.put(PATH + "/subscription", json=body)
    assert response.status_code == 200, response.text
    assert response.json()["public_key"] == before["public_key"]
    assert body["endpoint"] not in response.text and body["keys"]["auth"] not in response.text
    with app.state.database.connect() as db:
        row = db.execute("SELECT * FROM push_subscription").fetchone()
        assert (
            body["endpoint"] not in row["credentials"]
            and body["keys"]["auth"] not in row["credentials"]
        )
        assert (
            json.loads(app.state.reminders.vault.cipher.decrypt(row["credentials"].encode()))[
                "keys"
            ]
            == body["keys"]
        )
    restarted = Reminders(Database(app.state.database.root), app.state.database.root / "config")
    assert restarted.transport.public_key == before["public_key"]
    assert restarted.status(device).subscribed
    tokens = client.post(
        "/api/v1/auth/login",
        json={"username": "cook", "password": "a strong test password", "device_id": str(uuid4())},
    ).json()
    peer = {"Authorization": "Bearer " + tokens["access_token"]}
    assert client.get(PATH, headers=peer).json()["subscribed"] is False
    assert client.put(PATH + "/subscription", json=body, headers=peer).status_code == 409
    assert client.delete(PATH + "/subscription", headers=peer).status_code == 204
    assert client.get(PATH).json()["subscribed"] is True


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://web.push.apple.com/token",
        "https://127.0.0.1/token",
        "https://web.push.apple.com.evil.example/token",
        "https://x@web.push.apple.com/token",
        "https://web.push.apple.com:8080/token",
        "https://fcm.googleapis.com/a#secret",
        "https://fcm.googleapis.com/a\r\nX: value",
    ],
)
def test_untrusted_subscription_destinations_are_rejected_before_delivery(harness, endpoint):
    client, _, _, _ = harness
    body, _, _ = registration()
    body["endpoint"] = endpoint
    assert client.put(PATH + "/subscription", json=body).status_code == 422


def test_subscription_keys_and_civil_reminder_times_are_strictly_validated(harness):
    client, _, _, _ = harness
    body, _, _ = registration()
    invalid = {**body, "keys": {**body["keys"], "p256dh": encoded(b"x" * 65)}}
    assert client.put(PATH + "/subscription", json=invalid).status_code == 422
    assert client.put(PATH + "/subscription", json=body).status_code == 200
    for clock in ("25:00", "7:30", "18:00:00", "18:00+02:00"):
        assert (
            client.put(PATH + "/preferences", json={"preferences": {"dinner": clock}}).status_code
            == 422
        )
    assert (
        client.put(
            PATH + "/preferences",
            json={"preferences": {"breakfast": None, "lunch": None, "dinner": "18:00"}},
        ).status_code
        == 200
    )


def test_meal_delivery_deduplicates_and_keeps_household_content_out_of_payload(
    harness, mutation, monkeypatch
):
    service, job, _ = schedule(harness, mutation)
    calls = []
    monkeypatch.setattr(
        service.transport, "send", lambda *args: calls.append(args) or PushResponse(201)
    )
    service.enqueue_due(NOW)
    service.deliver(job, NOW)
    assert finish(service.database, job)
    service.deliver(job, NOW)
    service.enqueue_due(NOW)
    assert len(calls) == 1
    message = calls[0][1]
    assert message["title"] == "mealf" and message["url"] == "/app/?tab=calendar&day=2026-10-21"
    assert "Soup" not in json.dumps(message) and "Test household" not in json.dumps(message)
    with service.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM push_delivery").fetchone()[0] == 1
        assert (
            db.execute("SELECT state FROM background_job WHERE id=?", (job["id"],)).fetchone()[0]
            == "done"
        )


@pytest.mark.parametrize("change", ["delete", "cooked", "move", "disabled", "revoked", "late"])
def test_pending_reminders_recheck_current_meals_preferences_sessions_and_time(
    harness, mutation, monkeypatch, change
):
    service, job, meal = schedule(harness, mutation)
    client, _, _, _ = harness
    if change in ("delete", "cooked", "move"):
        value = dict(meal["payload"])
        if change == "cooked":
            value["cooked"] = True
        if change == "move":
            value["date"] = "2026-10-22"
        edit = mutation(
            meal["device_id"],
            kind="meal",
            entity_id=meal["entity_id"],
            base=2,
            payload=value,
            operation="delete" if change == "delete" else "upsert",
        )
        assert client.post("/api/v1/sync/push", json={"mutations": [edit]}).status_code == 200
    if change == "disabled":
        assert (
            client.put(PATH + "/preferences", json={"preferences": {"enabled": False}}).status_code
            == 200
        )
    if change == "revoked":
        with service.database.transaction() as db:
            db.execute("UPDATE session SET revoked=1")

    def forbidden(*args):
        raise AssertionError("Suppressed reminder reached the vendor transport")

    monkeypatch.setattr(service.transport, "send", forbidden)
    service.deliver(job, NOW.replace(hour=17) if change == "late" else NOW)


def test_failed_delivery_is_durable_and_expired_subscription_is_disabled(
    harness, mutation, monkeypatch
):
    service, job, _ = schedule(harness, mutation)
    monkeypatch.setattr(service.transport, "send", lambda *args: PushResponse(503))
    with pytest.raises(DomainError, match="push_provider_rejected"):
        service.deliver(job, NOW)
    finish(service.database, job, "push_provider_rejected")
    restarted = Database(service.database.root)
    with restarted.connect() as db:
        saved = db.execute("SELECT * FROM background_job WHERE id=?", (job["id"],)).fetchone()
        assert saved["state"] == "queued" and saved["attempts"] == 1
        assert db.execute("SELECT COUNT(*) FROM push_delivery").fetchone()[0] == 0
    monkeypatch.setattr(service.transport, "send", lambda *args: PushResponse(410))
    with pytest.raises(DomainError, match="push_subscription_expired"):
        service.deliver(job, NOW)
    assert not harness[0].get(PATH).json()["subscribed"]


def test_actual_encryption_and_vapid_signature_use_a_pinned_vendor_socket(harness, monkeypatch):
    _, app, _, _ = harness
    body, receiver, auth = registration()
    transport = app.state.reminders.transport
    sent = []

    class Response:
        status = 201

        def getheader(self, name):
            return None

        def close(self):
            pass

    class Connection:
        def __init__(self, host, address):
            assert host == "web.push.apple.com" and address == "17.0.0.1"

        def request(self, method, path, encrypted, headers):
            sent.append((method, path, encrypted, headers))

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr("mealf.webpush.public_addresses", lambda host, port: ["17.0.0.1"])
    monkeypatch.setattr("mealf.webpush.PinnedHTTPS", Connection)
    message = {"title": "mealf", "body": "Private test", "url": "/app/"}
    assert transport.send(body, message, "stable-tag", 900).status == 201
    method, path, encrypted, headers = sent[0]
    assert method == "POST" and path.startswith("/synthetic-")
    assert (
        json.loads(http_ece.decrypt(encrypted, private_key=receiver, auth_secret=auth)) == message
    )
    assert headers["Content-Encoding"] == "aes128gcm" and len(headers["Topic"]) == 32
    token, public = headers["Authorization"].removeprefix("vapid t=").split(",k=")

    def decode(value):
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    head, claims, signature = token.split(".")
    assert json.loads(decode(claims))["aud"] == "https://web.push.apple.com"
    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), decode(public))
    sig = decode(signature)
    key.verify(
        encode_dss_signature(int.from_bytes(sig[:32]), int.from_bytes(sig[32:])),
        (head + "." + claims).encode(),
        ec.ECDSA(hashes.SHA256()),
    )


def test_vendor_dns_rebinding_is_rejected_before_a_socket_is_created(harness, monkeypatch):
    body, _, _ = registration()
    monkeypatch.setattr(
        "mealf.importing.socket.getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("127.0.0.1", 443))],
    )
    with pytest.raises(DomainError, match="source_address_forbidden"):
        harness[1].state.reminders.transport.send(body, {"title": "mealf"}, "tag", 60)


def test_dst_gap_and_overlap_resolve_to_one_household_civil_occurrence():
    assert due_at(date(2026, 3, 29), "02:30", "Europe/Zurich") == datetime(
        2026, 3, 29, 1, 30, tzinfo=UTC
    )
    assert due_at(date(2026, 10, 25), "02:30", "Europe/Zurich") == datetime(
        2026, 10, 25, 0, 30, tzinfo=UTC
    )


def test_test_notification_replay_is_idempotent_and_preferences_can_disable_it(harness):
    client, app, _, _ = harness
    body, _, _ = registration()
    assert client.put(PATH + "/subscription", json=body).status_code == 200
    request = {"request_id": str(uuid4())}
    assert client.post(PATH + "/test", json=request).status_code == 202
    assert client.post(PATH + "/test", json=request).status_code == 202
    with app.state.database.connect() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM background_job WHERE kind='notification.test'"
            ).fetchone()[0]
            == 1
        )
    assert (
        client.put(PATH + "/preferences", json={"preferences": {"enabled": False}}).status_code
        == 200
    )
    assert client.post(PATH + "/test", json={"request_id": str(uuid4())}).status_code == 409
    assert client.delete(PATH + "/subscription").status_code == 204
    assert client.get(PATH).json()["subscribed"] is False


def test_vendor_retry_after_is_bounded_and_respected_by_durable_queue(
    harness, mutation, monkeypatch
):
    service, job, _ = schedule(harness, mutation)
    monkeypatch.setattr(service.transport, "send", lambda *args: PushResponse(429, 600))
    with pytest.raises(PushDeliveryError, match="push_rate_limited") as failure:
        service.deliver(job, NOW)
    import time

    before = time.time()
    assert finish(service.database, job, failure.value.code, retry_after=failure.value.retry_after)
    with service.database.connect() as db:
        saved = db.execute("SELECT * FROM background_job WHERE id=?", (job["id"],)).fetchone()
        assert saved["state"] == "queued" and saved["available_at"] >= before + 600
    assert retry_delay("120") == 120
    assert retry_delay("999999") == 3600
    assert retry_delay("nonsense") is None
    assert retry_delay("Wed, 21 Oct 2026 18:00:00") is None
    deadline = format_datetime(datetime.now(UTC) + timedelta(seconds=200), usegmt=True)
    assert 198 <= retry_delay(deadline) <= 200


def test_manual_retry_is_device_scoped_and_subscription_secrets_are_not_exported(harness):
    client, app, _, _ = harness
    body, _, _ = registration()
    assert client.put(PATH + "/subscription", json=body).status_code == 200
    assert client.post(PATH + "/test", json={"request_id": str(uuid4())}).status_code == 202
    tokens = client.post(
        "/api/v1/auth/login",
        json={"username": "cook", "password": "a strong test password", "device_id": str(uuid4())},
    ).json()
    peer = {"Authorization": "Bearer " + tokens["access_token"]}
    other, _, _ = registration()
    assert client.put(PATH + "/subscription", json=other, headers=peer).status_code == 200
    assert (
        client.post(PATH + "/test", json={"request_id": str(uuid4())}, headers=peer).status_code
        == 202
    )
    with app.state.database.transaction() as db:
        db.execute(
            "UPDATE background_job SET state='failed',attempts=8 WHERE kind='notification.test'"
        )
    assert client.post(PATH + "/retry").json() == {"state": "queued", "count": 1}
    assert client.get(PATH, headers=peer).json()["failed_jobs"] == 1
    exported = client.get("/api/v1/admin/export")
    assert exported.status_code == 200
    assert body["endpoint"] not in exported.text and body["keys"]["auth"] not in exported.text
    assert "webpush-vapid" not in exported.text and "push_subscription" not in exported.text


def test_push_controls_apply_browser_csrf_and_device_rate_limits(harness):
    from fastapi.testclient import TestClient

    from mealf.pwa_auth import AUTH_PATH, CSRF_COOKIE

    _, app, _, _ = harness
    with TestClient(app, base_url="https://kitchen.example") as browser:
        browser.headers.update({"Origin": "https://kitchen.example", "X-Mealf-Client": "pwa"})
        assert browser.get(PATH).status_code == 401
        signed = browser.post(
            AUTH_PATH + "/login",
            json={
                "username": "cook",
                "password": "a strong test password",
                "device_id": str(uuid4()),
            },
        )
        assert signed.status_code == 200
        body, _, _ = registration()
        assert browser.put(PATH + "/subscription", json=body).status_code == 403
        csrf = {"X-CSRF-Token": browser.cookies.get(CSRF_COOKIE)}
        assert browser.put(PATH + "/subscription", json=body, headers=csrf).status_code == 200
        assert browser.delete(PATH + "/subscription").status_code == 403
        for _ in range(10):
            assert (
                browser.post(
                    PATH + "/test", json={"request_id": str(uuid4())}, headers=csrf
                ).status_code
                == 202
            )
        limited = browser.post(PATH + "/test", json={"request_id": str(uuid4())}, headers=csrf)
        assert (
            limited.status_code == 429 and limited.json()["error"]["code"] == "push_request_limit"
        )


def test_expired_session_disables_future_reminders_without_deleting_preferences(harness, mutation):
    service, job, _ = schedule(harness, mutation)
    with service.database.transaction() as db:
        db.execute(
            "UPDATE session SET refresh_expires=0 WHERE id=(SELECT session_id FROM push_subscription)"
        )
    service.enqueue_due(NOW)
    service.deliver(job, NOW)
    with service.database.connect() as db:
        saved = db.execute("SELECT * FROM push_subscription").fetchone()
        assert saved["enabled"] == 0 and saved["error_code"] == "push_session_expired"
        assert json.loads(saved["preferences"])["dinner"] == "18:00"


def test_new_sign_in_must_explicitly_reconnect_a_revoked_notification_session(harness):
    client, app, device, tokens = harness
    body, _, _ = registration()
    assert client.put(PATH + "/subscription", json=body).status_code == 200
    fresh = client.post(
        "/api/v1/auth/login",
        json={"username": "cook", "password": "a strong test password", "device_id": device},
    ).json()
    with app.state.database.transaction() as db:
        db.execute("UPDATE session SET revoked=1 WHERE id=?", (tokens["session_id"],))
    headers = {"Authorization": "Bearer " + fresh["access_token"]}
    status = client.get(PATH, headers=headers).json()
    assert not status["subscribed"] and status["error_code"] == "push_session_expired"
    assert client.put(PATH + "/subscription", json=body, headers=headers).json()["subscribed"]


def test_subscription_cap_also_applies_when_reactivating_an_old_device(harness):
    client, app, _, tokens = harness
    body, _, _ = registration()
    assert client.put(PATH + "/subscription", json=body).status_code == 200
    with app.state.database.transaction() as db:
        db.execute("UPDATE push_subscription SET enabled=0")
        source = dict(db.execute("SELECT * FROM push_subscription LIMIT 1").fetchone())
        for index in range(50):
            device = str(uuid4())
            db.execute("INSERT INTO device VALUES (?,0)", (device,))
            db.execute(
                """INSERT INTO push_subscription(id,device_id,session_id,endpoint_hash,credentials,preferences,enabled,language,updated_at)
                VALUES(?,?,?,?,?,?,1,'en',0)""",
                (
                    str(uuid4()),
                    device,
                    tokens["session_id"],
                    str(index),
                    source["credentials"],
                    source["preferences"],
                ),
            )
    limited = client.put(PATH + "/subscription", json=body)
    assert (
        limited.status_code == 409 and limited.json()["error"]["code"] == "push_subscription_limit"
    )
