"""Isolated Docker E2E: real HTTP, restart persistence and clean-install restore.
Only creates/deletes uniquely named test containers and anonymous test volumes.
"""

import hashlib
import io
import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from PIL import Image

IMAGE = os.environ.get("MEALF_TEST_IMAGE", "mealf-server:development")
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
    return subprocess.check_output(
        DOCKER + list(args),
        text=True,
        env=env,
        stderr=subprocess.STDOUT if args[0] == "logs" else None,
    ).strip()


def setup_log_events(name):
    events = []
    for line in docker("logs", name).splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and entry.get("event") == "setup_required":
            events.append(entry)
    return events


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
        name = "mealf-test-" + str(uuid4())
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
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            try:
                if request(base, "/api/v1/system/health")["status"] == "ok":
                    break
            except (URLError, ConnectionError, TimeoutError):
                time.sleep(0.25)
        else:
            # Only synthetic test containers: preserve bounded startup diagnostics on failure.
            raise RuntimeError(
                "Container readiness timed out: " + docker("logs", "--tail", "40", name)
            )
        assert docker("inspect", "--format", "{{.Config.User}}", name) == "10001:10001"
        helper = request(base, "/api/v1/integrations/chatgpt/helper")
        assert helper == Path("src/mealf/chatgpt_helper.py").read_bytes()
        shell = request(base, "/app/")
        assert b"manifest.webmanifest" in shell and b"/app/assets/" in shell
        assert json.loads(request(base, "/app/manifest.webmanifest"))["start_url"] == "/app/"
        worker = request(base, "/app/sw.js")
        assert b"mealf-shell-" in worker and b"/api/v1/" not in worker
        assert request(base, "/app/icon-192.png").startswith(b"\x89PNG")
        identity = json.loads(request(base, "/app/manifest.webmanifest"))
        assert identity["id"] == identity["scope"] == "/app/"
        assert identity["icons"][0]["src"] == "/app/brand/icon-192-v1.png"
        assert any(icon["purpose"] == "maskable" for icon in identity["icons"])
        brand = request(base, "/app/brand/provenance.json")
        for path, expected in brand["outputs"].items():
            content = request(base, "/app/" + path)
            assert hashlib.sha256(content).hexdigest() == expected["sha256"]
        assert b"/app/brand/wordmark-v1.png" in request(base, "/admin/")
        # The installed wheel must ship the console's palette, not only the Vite bundle.
        assert request(base, "/app/theme.css") == Path("frontend/src/tokens.css").read_bytes()
        assert b"/app/theme.css" in request(base, "/admin/console.css")
        assert (
            request(base, "/app/appearance.js")
            == Path("frontend/public/appearance.js").read_bytes()
        )
        assert b"/app/appearance.js" in request(base, "/app/")
        assert b"/app/appearance.js" in request(base, "/admin/")
        # Shared peach interaction must ship in the wheel and the installed PWA shell.
        assert b"/app/peach.js" in shell and b"/app/peach.css" in shell
        assert b"/app/peach.js" in request(base, "/admin/")
        assert b"peach.animate" in request(base, "/app/peach.js")
        assert b"prefers-reduced-motion" in request(base, "/app/peach.css")
        # NAS/container consoles may require Bash. The same non-root account must
        # be able to read its private bootstrap token through an actual Bash process.
        version = docker("exec", name, "/bin/bash", "--version")
        assert "GNU bash, version 5.3.9" in version and "Free Software Foundation" in version
        assert (
            docker(
                "exec",
                name,
                "python",
                "-c",
                "from mealf.source_images import bounded_source_photo; "
                "assert bounded_source_photo('http://127.0.0.1/private', None) is None; "
                "print('source-photo-isolation-ok')",
            )
            == "source-photo-isolation-ok"
        )
        assert (
            docker(
                "exec",
                "-t",
                name,
                "/bin/bash",
                "--noprofile",
                "--norc",
                "-c",
                "test -t 1 && printf mealf-bash-terminal",
            )
            == "mealf-bash-terminal"
        )
        events = setup_log_events(name)
        assert len(events) == 1
        token = events[0]["setup_token"]
        assert token == docker("exec", name, "/bin/bash", "-lc", "cat /data/config/setup-token")
        assert token == docker("exec", name, "cat", "/data/config/setup-token")
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
        # Exercise account ownership and authorization in the installed non-root image.
        admin = request(base, "/api/v1/auth/me", headers=headers)
        assert admin["role"] == "admin" and admin["active"]
        member = request(
            base,
            "/api/v1/admin/users",
            {
                "username": "member",
                "password": "synthetic member container password",
                "role": "user",
            },
            headers,
        )
        member_credentials = {
            "username": "member",
            "password": "synthetic member container password",
            "device_id": str(uuid4()),
        }
        member_tokens = request(base, "/api/v1/auth/login", member_credentials)
        member_headers = {"Authorization": "Bearer " + member_tokens["access_token"]}
        assert request(base, "/api/v1/auth/me", headers=member_headers) == member
        assert request(base, "/api/v1/household", headers=member_headers) == request(
            base, "/api/v1/household", headers=headers
        )
        for endpoint in ["/api/v1/admin/users", "/api/v1/admin/ai", "/api/v1/admin/export"]:
            try:
                request(base, endpoint, headers=member_headers)
                raise AssertionError("Regular user accessed " + endpoint)
            except HTTPError as failure:
                assert failure.code == 403
        assert request(base, "/api/v1/ai/status", headers=member_headers)["enabled"] is False
        maintenance_preview = json.loads(
            docker("exec", name, "python", "-m", "mealf.cli", "cleanup", "--dry-run")
        )
        assert maintenance_preview["dry_run"] is True
        assert (
            json.loads(docker("exec", name, "python", "-m", "mealf.cli", "cleanup"))["dry_run"]
            is False
        )
        push_before = request(base, "/api/v1/notifications/push", headers=headers)
        assert not push_before["subscribed"] and len(push_before["public_key"]) == 87
        notice = docker(
            "exec",
            name,
            "python",
            "-c",
            "from importlib.resources import files; print(files('mealf').joinpath('attributions/http-ece-1.2.1.LICENSE').read_text())",
        )
        assert "Martin Thomson" in notice and "MIT" in notice
        bash_license = docker(
            "exec",
            name,
            "python",
            "-c",
            "from importlib.resources import files; print(files('mealf').joinpath('attributions/bash-GPL-3.LICENSE').read_text())",
        )
        assert "GNU GENERAL PUBLIC LICENSE" in bash_license and "Version 3" in bash_license
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
        boundary = "mealf-smoke-boundary"
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
        planning_path = "/api/v1/household/planning-preferences"
        planning_update = {
            "request_id": str(uuid4()),
            "base_revision": 0,
            "preferences": {"categories": ["lunch"], "servings": "3.5", "use_leftovers": False},
        }
        planning_receipt = request(base, planning_path, planning_update, headers, "PUT")
        assert request(base, planning_path, planning_update, headers, "PUT") == planning_receipt
        planning_before = request(base, planning_path, headers=headers)
        assert planning_before["accepted_counts"] == {recipe["entity_id"]: 1}
        projection = request(base, "/api/v1/planning/shopping-projection", headers=headers)
        assert projection["requirements"][0]["spec"] == "600 g"
        shopping = request(base, "/api/v1/planning/shopping", headers=headers)
        assert shopping["connection_state"] == "not_configured"
        assert shopping["requirements"][0]["spec"] == "600 g"
        assert shopping["requirements"][0]["state"] == "not_sent"
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
        food_path = "/api/v1/household/food-profile"
        food_write = {
            "request_id": str(uuid4()),
            "base_revision": 0,
            "patch": {
                "likes": ["pasta"],
                "dislikes": ["mushrooms"],
                "taste_setup_done": True,
                "pantry_setup_done": True,
            },
        }
        food_receipt = request(base, food_path, food_write, headers, "PUT")
        food_before = request(base, food_path, headers=headers)
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
        # Docker retains old log lines. Configured restarts must not add token entries.
        assert len(setup_log_events(name)) == 1
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
        assert request(base, "/api/v1/auth/me", headers=member_headers) == member
        assert request(base, "/api/v1/recipes", headers=member_headers) == request(
            base, "/api/v1/recipes", headers=headers
        )
        changed = request(
            base, "/api/v1/admin/users/" + member["id"], {"active": False}, headers, "PATCH"
        )
        assert changed["active"] is False
        for endpoint, body, auth in [
            ("/api/v1/auth/me", None, member_headers),
            ("/api/v1/auth/refresh", {"refresh_token": member_tokens["refresh_token"]}, None),
            ("/api/v1/auth/login", member_credentials, None),
        ]:
            try:
                request(base, endpoint, body, auth)
                raise AssertionError("Disabled account retained a capability")
            except HTTPError as failure:
                assert failure.code == 401
        assert request(base, "/api/v1/auth/me", headers=headers) == admin
        assert request(base, food_path, headers=headers) == food_before
        assert request(base, food_path, food_write, headers, "PUT") == food_receipt
        restored_ai = request(base, "/api/v1/admin/ai", headers=headers)
        assert request(base, planning_path, headers=headers) == planning_before
        assert (
            request(base, "/api/v1/notifications/push", headers=headers)["public_key"]
            == push_before["public_key"]
        )
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
        before_import = request(base, "/api/v1/recipes", headers=headers)["items"]
        capabilities = request(base, "/api/v1/system/capabilities")
        assert capabilities["image_recipe_import"] is True
        assert capabilities["image_import_languages"] == ["en", "de"]
        # Exercise the packaged native OCR engine/models on both CPU architectures.
        # Previews remain separate from recipes until explicitly confirmed.
        for language, title in [("en", "Lemon rice"), ("de", "Tomatenreis")]:
            document_id = str(uuid4())
            document = Path("tests/fixtures/recipe-photo-" + language + ".png").read_bytes()
            multipart = (
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="recipe.png"\r\nContent-Type: image/png\r\n\r\n'.encode()
                + document
                + f"\r\n--{boundary}--\r\n".encode()
            )
            request(base, "/api/v1/media/" + document_id, multipart, upload_headers, "PUT")
            pending_image = request(
                base,
                "/api/v1/imports",
                {"request_id": str(uuid4()), "image_id": document_id},
                headers,
            )
            for _ in range(150):
                image_draft = request(
                    base, "/api/v1/imports/" + pending_image["id"], headers=headers
                )
                if image_draft["state"] == "preview":
                    break
                assert image_draft["state"] != "needs_input", image_draft.get("error_code")
                time.sleep(0.2)
            else:
                raise AssertionError("Packaged OCR did not produce a preview")
            assert image_draft["recipe"]["title"] == title
            assert image_draft["recipe"]["image_id"] == document_id
            assert image_draft["recipe"]["ingredients"][0]["quantity"] == "200"
            assert image_draft["recognized_text"]
            assert request(base, "/api/v1/recipes", headers=headers)["items"] == before_import
            request(
                base, "/api/v1/imports/" + pending_image["id"], headers=headers, method="DELETE"
            )
        importing = request(
            base,
            "/api/v1/imports",
            {
                "request_id": str(uuid4()),
                "text": json.dumps(
                    {
                        "@type": "Recipe",
                        "name": "Imported bread",
                        "recipeYield": "2",
                        "recipeIngredient": ["½ kg flour", "salt to taste"],
                        "recipeInstructions": ["Mix and bake"],
                    }
                ),
            },
            headers,
        )
        for _ in range(80):
            draft = request(base, "/api/v1/imports/" + importing["id"], headers=headers)
            if draft["state"] == "preview":
                break
            assert draft["state"] not in ("needs_input", "failed"), draft
            time.sleep(0.2)
        else:
            raise AssertionError("Import worker did not produce a reviewable preview")
        assert request(base, "/api/v1/recipes", headers=headers)["items"] == before_import
        assert draft["recipe"]["ingredients"][0]["quantity"] == "0.5"
        assert draft["recipe"]["ingredients"][0]["original_text"] == "½ kg flour"
        reviewed = mutation(device, "recipe", draft["recipe"])
        request(base, "/api/v1/imports/" + importing["id"] + "/confirm", reviewed, headers)
        imported = request(base, "/api/v1/recipes/" + reviewed["entity_id"], headers=headers)
        assert imported["payload"]["title"] == "Imported bread"
        exported = request(base, "/api/v1/admin/export", headers=headers)
        assert (
            exported["version"] == 4
            and exported["accepted_suggestions"] == planning_before["accepted_counts"]
        )
        assert exported["food_profile"] == food_before["profile"]
        assert ai_credential not in json.dumps(exported)
        _, other, _, other_headers = start()
        assert request(other, "/api/v1/admin/import", exported, other_headers)["imported"] == len(
            exported["entities"]
        )
        assert request(other, food_path, headers=other_headers)["profile"] == food_before["profile"]
        restored = request(other, "/api/v1/planning/shopping-projection", headers=other_headers)
        assert (
            request(other, planning_path, headers=other_headers)["preferences"]
            == planning_before["preferences"]
        )
        assert (
            request(other, planning_path, headers=other_headers)["accepted_counts"]
            == planning_before["accepted_counts"]
        )
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
        assert (
            request(third, planning_path, headers=third_headers)["preferences"]
            == planning_before["preferences"]
        )
        assert (
            request(third, planning_path, headers=third_headers)["accepted_counts"]
            == planning_before["accepted_counts"]
        )
        assert request(third, "/api/v1/media/" + image_id, headers=third_headers) == canonical_photo
        print(
            "PASS: non-root/read-only Docker, bootstrap, household admin/user roles and shared content, denied admin access, persisted account sessions and isolated disable/revocation, HTTP auth, rotated-capability revocation across restart with another active session preserved, idempotent sync, recipe/meal projection, restart, offline replay, immutable photo upload, leftover exclusion, suggestion approval/replay across restart, encrypted AI settings persistence/redaction, stable history proofs and anchored snapshot pages, durable fractional-ingredient import preview and explicit confirmation, JSON and streamed archive restore."
        )
    finally:
        for name in containers:
            docker("rm", "-f", "-v", name)


if __name__ == "__main__":
    main()
