"""Isolated Docker E2E: real HTTP, restart persistence and clean-install restore.
Only creates/deletes uniquely named test containers and anonymous test volumes.
"""

import io
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from PIL import Image

IMAGE = os.environ.get("AIRCOOKER_TEST_IMAGE", "aircooker-server:development")
DOCKER = ["docker", "--host=unix:///var/run/docker.sock"]


def docker(*args):
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in (
            "DOCKER_HOST",
            "DOCKER_CONTEXT",
            "DOCKER_TLS",
            "DOCKER_TLS_VERIFY",
            "DOCKER_CERT_PATH",
        )
    }
    return subprocess.check_output(DOCKER + list(args), text=True, env=env).strip()


def request(base, path, body=None, headers=None, method=None):
    raw = body if isinstance(body, bytes) else None if body is None else json.dumps(body).encode()
    req = Request(
        base + path,
        data=raw,
        headers={"Content-Type": "application/json", **(headers or {})},
        method=method,
    )
    with urlopen(req, timeout=10) as response:
        content = response.read()
        if not content:
            return None
        return (
            json.loads(content)
            if response.headers.get_content_type() == "application/json"
            else content
        )


def mutation(device, kind, payload, eid=None, base=0):
    mid = str(uuid4())
    return {
        "mutation_id": mid,
        "idempotency_key": mid,
        "entity_id": eid or str(uuid4()),
        "kind": kind,
        "operation": "upsert",
        "base_revision": base,
        "payload": payload,
        "device_id": device,
        "client_timestamp": "1990-01-01T00:00:00Z",
    }


def main():
    containers = []

    def start():
        name = "aircooker-test-" + str(uuid4())
        docker(
            "run",
            "-d",
            "--name",
            name,
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--tmpfs",
            "/tmp:size=64m",
            "-p",
            "127.0.0.1::8080",
            IMAGE,
        )
        containers.append(name)
        port = docker("port", name, "8080/tcp").rsplit(":", 1)[1]
        base = "http://127.0.0.1:" + port
        for _ in range(60):
            try:
                if request(base, "/api/v1/system/health")["status"] == "ok":
                    break
            except (URLError, ConnectionError, TimeoutError):
                time.sleep(0.25)
        else:
            raise RuntimeError("Container readiness timed out")
        assert docker("inspect", "--format", "{{.Config.User}}", name) == "10001:10001"
        token = docker("exec", name, "cat", "/data/config/setup-token")
        device = str(uuid4())
        credentials = {
            "username": "cook",
            "password": "synthetic smoke test password",
            "device_id": device,
            "name": "Smoke household",
            "timezone": "UTC",
            "language": "en",
        }
        session = request(base, "/api/v1/setup", credentials, {"X-Setup-Token": token})
        return name, base, device, {"Authorization": "Bearer " + session["access_token"]}

    try:
        name, base, device, headers = start()
        logout_session = request(
            base,
            "/api/v1/auth/login",
            {
                "username": "cook",
                "password": "synthetic smoke test password",
                "device_id": str(uuid4()),
            },
        )
        rotated_session = request(
            base,
            "/api/v1/auth/refresh",
            {
                "refresh_token": logout_session["refresh_token"],
            },
        )
        for _ in range(2):
            assert (
                request(
                    base,
                    "/api/v1/auth/revoke",
                    {
                        "refresh_token": logout_session["refresh_token"],
                    },
                )
                is None
            )
        image_id = str(uuid4())
        photo = io.BytesIO()
        Image.new("RGB", (12, 12), "orange").save(photo, format="PNG")
        boundary = "aircooker-smoke-boundary"
        upload = (
            (
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="photo.png"\r\n'
                "Content-Type: image/png\r\n\r\n"
            ).encode()
            + photo.getvalue()
            + f"\r\n--{boundary}--\r\n".encode()
        )
        upload_headers = {**headers, "Content-Type": "multipart/form-data; boundary=" + boundary}
        info = request(base, "/api/v1/media/" + image_id, upload, upload_headers, "PUT")
        assert info["content_type"] == "image/jpeg"
        assert request(base, "/api/v1/media/" + image_id, upload, upload_headers, "PUT") == info
        canonical_photo = request(base, "/api/v1/media/" + image_id, headers=headers)
        recipe = mutation(
            device,
            "recipe",
            {
                "title": "Smoke soup",
                "image_id": image_id,
                "servings": "2",
                "ingredients": [
                    {"id": str(uuid4()), "name": "Carrots", "quantity": "200", "unit": "g"}
                ],
                "steps": ["Cook"],
            },
        )
        result = request(base, "/api/v1/sync/push", {"mutations": [recipe]}, headers)
        assert request(base, "/api/v1/sync/push", {"mutations": [recipe]}, headers) == result
        today = str(datetime.now(UTC).date())
        meal = mutation(
            device,
            "meal",
            {
                "recipe_id": recipe["entity_id"],
                "date": today,
                "category": "dinner",
                "servings": "4",
            },
        )
        request(base, "/api/v1/sync/push", {"mutations": [meal]}, headers)
        leftover = mutation(
            device,
            "leftover",
            {
                "recipe_id": recipe["entity_id"],
                "produced_on": today,
                "portions": "2",
            },
        )
        request(base, "/api/v1/sync/push", {"mutations": [leftover]}, headers)
        reheated = mutation(
            device,
            "meal",
            {
                "recipe_id": recipe["entity_id"],
                "leftover_id": leftover["entity_id"],
                "date": today,
                "category": "lunch",
                "servings": "2",
            },
        )
        request(base, "/api/v1/sync/push", {"mutations": [reheated]}, headers)
        from datetime import date, timedelta

        day = date.fromisoformat(today)
        monday = str(day - timedelta(days=day.weekday()))
        preview = request(
            base,
            "/api/v1/suggestions/weekly?monday=" + monday + "&allow_repeats=true",
            headers=headers,
            method="POST",
        )
        suggestion = {k: v for k, v in preview["meals"][0].items() if k != "reasons"}
        approval = {
            "request_id": str(uuid4()),
            "monday": monday,
            "basis": preview["basis"],
            "mutations": [mutation(device, "meal", suggestion)],
        }
        applied = request(base, "/api/v1/suggestions/apply", approval, headers)
        assert request(base, "/api/v1/suggestions/apply", approval, headers) == applied
        projection = request(base, "/api/v1/planning/shopping-projection", headers=headers)
        assert projection["requirements"][0]["spec"] == "600 g"
        ai_credential = "synthetic container AI credential"
        configured_ai = request(
            base,
            "/api/v1/admin/ai",
            {
                "provider": "openai-compatible",
                "base_url": "https://ai.example/v1",
                "model": "container-test",
                "api_key": ai_credential,
            },
            headers,
            "PUT",
        )
        assert configured_ai["enabled"] and configured_ai["key_configured"]
        assert ai_credential not in json.dumps(configured_ai)
        history = request(base, "/api/v1/sync/state", headers=headers)
        checkpoint = {"cursor": history["cursor"], "token": history["token"]}
        page = request(
            base, "/api/v1/sync/snapshot?" + urlencode({**checkpoint, "limit": 1}), headers=headers
        )
        snapshot_rows = page["changes"]
        docker("restart", name)
        base = "http://127.0.0.1:" + docker("port", name, "8080/tcp").rsplit(":", 1)[1]
        for _ in range(60):
            try:
                if request(base, "/api/v1/system/health")["status"] == "ok":
                    break
            except (URLError, ConnectionError, TimeoutError):
                time.sleep(0.25)
        try:
            request(
                base,
                "/api/v1/recipes",
                headers={
                    "Authorization": "Bearer " + rotated_session["access_token"],
                },
            )
            raise AssertionError("Revoked session survived restart")
        except HTTPError as failure:
            assert failure.code == 401
        restored_ai = request(base, "/api/v1/admin/ai", headers=headers)
        assert (
            restored_ai["enabled"]
            and restored_ai["key_configured"]
            and restored_ai["origin"] == "saved"
        )
        assert request(base, "/api/v1/suggestions/apply", approval, headers) == applied
        after_restart = request(
            base, "/api/v1/sync/state?cursor=" + str(checkpoint["cursor"]), headers=headers
        )
        assert after_restart["requested_token"] == checkpoint["token"]
        edit = mutation(
            device,
            "recipe",
            {**recipe["payload"], "title": "Offline edit replayed"},
            eid=recipe["entity_id"],
            base=result[0]["revision"],
        )
        accepted = request(
            base, "/api/v1/sync/push", {"mutations": [edit], "checkpoint": checkpoint}, headers
        )
        assert len(accepted[0]["revision_token"]) == 32
        delta = request(base, "/api/v1/sync/pull?" + urlencode(checkpoint), headers=headers)
        assert delta["cursor_token"] == accepted[0]["revision_token"]
        while page["next_after"]:
            page = request(
                base,
                "/api/v1/sync/snapshot?"
                + urlencode({**checkpoint, "limit": 1, "after": page["next_after"]}),
                headers=headers,
            )
            snapshot_rows.extend(page["changes"])
        assert (
            next(row for row in snapshot_rows if row["kind"] == "recipe")["payload"]["title"]
            == "Smoke soup"
        )
        wrong_token = ("0" if checkpoint["token"][0] != "0" else "1") + checkpoint["token"][1:]
        try:
            request(
                base,
                "/api/v1/sync/push",
                {"mutations": [edit], "checkpoint": {**checkpoint, "token": wrong_token}},
                headers,
            )
            raise AssertionError("Stale history proof unexpectedly accepted")
        except HTTPError as failure:
            assert failure.code == 409
        assert (
            request(base, "/api/v1/recipes/" + recipe["entity_id"], headers=headers)["payload"][
                "title"
            ]
            == "Offline edit replayed"
        )
        assert request(base, "/api/v1/media/" + image_id, headers=headers) == canonical_photo
        exported = request(base, "/api/v1/admin/export", headers=headers)
        assert ai_credential not in json.dumps(exported)
        _, other, _, other_headers = start()
        assert request(other, "/api/v1/admin/import", exported, other_headers)["imported"] == len(
            exported["entities"]
        )
        restored = request(other, "/api/v1/planning/shopping-projection", headers=other_headers)
        assert restored["requirements"][0]["spec"] == "600 g"
        assert request(other, "/api/v1/media/" + image_id, headers=other_headers) == canonical_photo
        archive = request(base, "/api/v1/admin/export/archive", headers=headers)
        _, third, _, third_headers = start()
        restored_archive = request(
            third,
            "/api/v1/admin/import/archive",
            archive,
            {**third_headers, "Content-Type": "application/zip"},
            "POST",
        )
        assert restored_archive == {"imported": len(exported["entities"]), "media_imported": 1}
        assert request(third, "/api/v1/media/" + image_id, headers=third_headers) == canonical_photo
        print(
            "PASS: non-root/read-only Docker, bootstrap, HTTP auth, rotated-capability revocation across restart with another active session preserved, idempotent sync, recipe/meal projection, restart, offline replay, immutable photo upload, leftover exclusion, suggestion approval/replay across restart, encrypted AI settings persistence/redaction, stable history proofs and anchored snapshot pages, JSON and streamed archive restore."
        )
    finally:
        for name in containers:
            docker("rm", "-f", "-v", name)


if __name__ == "__main__":
    main()
