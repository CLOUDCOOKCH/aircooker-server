import hashlib
import io
import json
import zipfile
from contextlib import contextmanager
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

from aircooker.app import create_app


def png(colour="orange", size=(60, 40)):
    output = io.BytesIO()
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Location", "synthetic private metadata")
    Image.new("RGB", size, colour).save(output, format="PNG", pnginfo=metadata)
    return output.getvalue()


def upload(client, image_id=None, data=None, content_type="image/png"):
    return client.put(
        "/api/v1/media/" + (image_id or str(uuid4())),
        files={"file": ("untrusted-name.png", data or png(), content_type)},
    )


@contextmanager
def clean_client(path):
    app = create_app(path, run_worker=False)
    with TestClient(app) as client:
        device = str(uuid4())
        token = (path / "config" / "setup-token").read_text()
        response = client.post(
            "/api/v1/setup",
            headers={"X-Setup-Token": token},
            json={
                "name": "Clean household",
                "username": "cook",
                "password": "synthetic restore password",
                "device_id": device,
                "timezone": "UTC",
                "language": "en",
            },
        )
        assert response.status_code == 201, response.text
        client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        yield client, app, device


def save_recipe(client, mutation, device, image_id=None):
    item = mutation(device, payload={"title": "Photo recipe", "image_id": image_id})
    response = client.post("/api/v1/sync/push", json={"mutations": [item]})
    assert response.status_code == 200, response.text
    return item, response.json()[0]["revision"]


def test_photo_normalisation_metadata_and_idempotent_replay(harness):
    client, app, _, _ = harness
    image_id = str(uuid4())
    response = upload(client, image_id, png(size=(3000, 1000)))
    assert response.status_code == 200, response.text
    info = response.json()
    assert info["width"] == 2048 and info["height"] <= 2048
    downloaded = client.get("/api/v1/media/" + image_id)
    assert downloaded.headers["content-type"] == "image/jpeg"
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    assert hashlib.sha256(downloaded.content).hexdigest() == info["sha256"]
    assert len(downloaded.content) == info["byte_count"]
    with Image.open(io.BytesIO(downloaded.content)) as image:
        assert image.format == "JPEG" and not image.getexif()
        assert "Location" not in image.info and "exif" not in image.info
    assert upload(client, image_id, png(size=(3000, 1000))).json() == info
    assert upload(client, image_id, downloaded.content, "image/jpeg").json() == info
    assert upload(client, image_id, png("green")).status_code == 409
    with app.state.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM recipe_media").fetchone()[0] == 1


def test_photo_authentication_and_missing_media(harness):
    client, _, _, _ = harness
    client.headers.pop("Authorization")
    assert upload(client).status_code == 401
    assert client.get("/api/v1/media/" + str(uuid4())).status_code == 401


@pytest.mark.parametrize(
    ("data", "content_type", "status"),
    [
        (b'<svg xmlns="http://www.w3.org/2000/svg"/>', "image/svg+xml", 415),
        (b"<html>not a photograph</html>", "image/jpeg", 422),
        (png(), "image/jpeg", 422),
    ],
)
def test_untrusted_upload_types_are_rejected(harness, data, content_type, status):
    client, app, _, _ = harness
    assert upload(client, data=data, content_type=content_type).status_code == status
    with app.state.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM recipe_media").fetchone()[0] == 0


def test_image_and_storage_limits_leave_no_asset(harness, monkeypatch):
    client, app, _, _ = harness
    monkeypatch.setattr("aircooker.media.MAX_PIXELS", 10)
    assert upload(client).json()["error"]["code"] == "image_pixel_limit"
    monkeypatch.setattr("aircooker.media.MAX_PIXELS", 16_000_000)
    monkeypatch.setattr("aircooker.media.MAX_TOTAL_BYTES", 1)
    assert upload(client).json()["error"]["code"] == "media_storage_limit"
    with app.state.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM recipe_media").fetchone()[0] == 0


def test_unknown_recipe_photo_rejected_transactionally(harness, mutation):
    client, _, device, _ = harness
    item = mutation(device, payload={"title": "No asset yet", "image_id": str(uuid4())})
    response = client.post("/api/v1/sync/push", json={"mutations": [item]})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "recipe_image_not_found"
    assert client.get("/api/v1/recipes").json()["items"] == []


def test_json_export_restores_exact_photo(harness, mutation, tmp_path):
    client, _, device, _ = harness
    info = upload(client).json()
    recipe, _ = save_recipe(client, mutation, device, info["id"])
    original = client.get("/api/v1/media/" + info["id"]).content
    exported = client.get("/api/v1/admin/export").json()
    assert exported["version"] == 2 and len(exported["media"]) == 1
    with clean_client(tmp_path / "restored") as (target, _, _):
        response = target.post("/api/v1/admin/import", json=exported)
        assert response.status_code == 200, response.text
        assert response.json()["media_imported"] == 1
        assert target.get("/api/v1/media/" + info["id"]).content == original
        assert (
            target.get("/api/v1/recipes/" + recipe["entity_id"]).json()["payload"]["image_id"]
            == info["id"]
        )


def test_archive_roundtrip_and_deleted_recipe_history(harness, mutation, tmp_path):
    client, app, device, _ = harness
    info = upload(client).json()
    recipe, revision = save_recipe(client, mutation, device, info["id"])
    meal = mutation(
        device,
        kind="meal",
        payload={"recipe_id": recipe["entity_id"], "date": "2026-10-19", "category": "dinner"},
    )
    assert client.post("/api/v1/sync/push", json={"mutations": [meal]}).status_code == 200
    deletion = mutation(device, entity_id=recipe["entity_id"], base=revision, operation="delete")
    assert client.post("/api/v1/sync/push", json={"mutations": [deletion]}).status_code == 200
    response = client.get("/api/v1/admin/export/archive")
    assert response.status_code == 200 and response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == {"manifest.json", "media/" + info["id"] + ".jpg"}
    assert not list((app.state.database.root / "jobs").glob(".export-*"))
    with clean_client(tmp_path / "restored") as (target, target_app, _):
        restored = target.post(
            "/api/v1/admin/import/archive",
            content=response.content,
            headers={"Content-Type": "application/zip"},
        )
        assert restored.status_code == 200, restored.text
        assert restored.json()["imported"] == 2
        assert target.get("/api/v1/recipes/" + recipe["entity_id"]).status_code == 404
        assert len(target.get("/api/v1/calendar/meals").json()["items"]) == 1
        assert (
            target.get("/api/v1/media/" + info["id"]).content
            == client.get("/api/v1/media/" + info["id"]).content
        )
        assert not list((target_app.state.database.root / "jobs").glob(".restore-*"))


def test_archive_conflict_rolls_back_media_and_settings(harness, mutation, tmp_path):
    client, _, device, _ = harness
    info = upload(client).json()
    recipe, _ = save_recipe(client, mutation, device, info["id"])
    exported = client.get("/api/v1/admin/export/archive").content
    with clean_client(tmp_path / "target") as (target, target_app, target_device):
        collision = mutation(
            target_device, entity_id=recipe["entity_id"], payload={"title": "Keep this"}
        )
        assert target.post("/api/v1/sync/push", json={"mutations": [collision]}).status_code == 200
        response = target.post(
            "/api/v1/admin/import/archive",
            content=exported,
            headers={"Content-Type": "application/zip"},
        )
        assert response.status_code == 409
        assert target.get("/api/v1/household").json()["name"] == "Clean household"
        assert target.get("/api/v1/media/" + info["id"]).status_code == 404
        with target_app.state.database.connect() as db:
            assert db.execute("SELECT COUNT(*) FROM recipe_media").fetchone()[0] == 0


def test_archive_traversal_and_corruption_are_rejected(harness):
    client, app, _, _ = harness
    manifest = client.get("/api/v1/admin/export").json()
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(
                {
                    "format": "aircooker-household-archive",
                    "version": 1,
                    "household": manifest,
                    "media": [],
                }
            ),
        )
        archive.writestr("../escape.txt", "untrusted")
    response = client.post(
        "/api/v1/admin/import/archive",
        content=output.getvalue(),
        headers={"Content-Type": "application/zip"},
    )
    assert (
        response.status_code == 422
        and response.json()["error"]["code"] == "archive_unexpected_entries"
    )
    assert not (app.state.database.root / "escape.txt").exists()
    response = client.post(
        "/api/v1/admin/import/archive",
        content=b"not a zip",
        headers={"Content-Type": "application/zip"},
    )
    assert response.status_code == 422 and response.json()["error"]["code"] == "archive_invalid"


def test_imported_recipe_provenance_does_not_require_old_jobs(harness, mutation, tmp_path):
    client, _, device, _ = harness
    # A version-one export from a different installation can contain its import provenance.
    exported = client.get("/api/v1/admin/export").json()
    item = mutation(device, payload={"title": "Restored import"})
    exported["version"] = 1
    exported["entities"] = [
        {
            "kind": "recipe",
            "id": item["entity_id"],
            "payload": {
                "title": "Restored import",
                "provenance": {"import_job_id": str(uuid4()), "reviewed_by_user": "true"},
            },
        }
    ]
    with clean_client(tmp_path / "restored") as (target, _, _):
        response = target.post("/api/v1/admin/import", json=exported)
        assert response.status_code == 200, response.text
        assert (
            target.get("/api/v1/recipes/" + item["entity_id"]).json()["payload"]["title"]
            == "Restored import"
        )


def test_photo_and_archive_cookie_mutations_require_csrf(harness):
    _, app, _, _ = harness
    with TestClient(app, base_url="https://localhost") as browser:
        login = browser.post(
            "/api/v1/admin/login",
            json={
                "username": "cook",
                "password": "a strong test password",
                "device_id": str(uuid4()),
            },
            headers={"Origin": "https://localhost"},
        )
        assert login.status_code == 200
        assert upload(browser).status_code == 403
        assert (
            browser.post(
                "/api/v1/admin/import/archive",
                content=b"unused",
                headers={"Content-Type": "application/zip"},
            ).status_code
            == 403
        )
        browser.headers.update(
            {"Origin": "https://localhost", "X-CSRF-Token": browser.cookies["aircooker_csrf"]}
        )
        assert upload(browser).status_code == 200


def test_corrupt_archive_image_rolls_back_everything(harness, mutation, tmp_path):
    client, _, device, _ = harness
    info = upload(client).json()
    save_recipe(client, mutation, device, info["id"])
    raw = client.get("/api/v1/admin/export/archive").content
    corrupt = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as source, zipfile.ZipFile(corrupt, "w") as target:
        for name in source.namelist():
            data = source.read(name)
            if name.endswith(".jpg"):
                data = data[:-1] + bytes([data[-1] ^ 1])
            target.writestr(name, data)
    with clean_client(tmp_path / "target") as (target, target_app, _):
        response = target.post(
            "/api/v1/admin/import/archive",
            content=corrupt.getvalue(),
            headers={"Content-Type": "application/zip"},
        )
        assert response.status_code == 422
        assert target.get("/api/v1/recipes").json()["items"] == []
        assert target.get("/api/v1/media/" + info["id"]).status_code == 404
        assert not list((target_app.state.database.root / "jobs").glob(".restore-*"))


def test_streamed_archive_and_photo_size_limits(harness, monkeypatch):
    client, app, _, _ = harness
    # No Content-Length: exercise the streaming counter, not only the header check.
    monkeypatch.setattr("aircooker.app.MAX_ARCHIVE", 16)
    response = client.post(
        "/api/v1/admin/import/archive",
        content=iter([b"x" * 10, b"y" * 10]),
        headers={"Content-Type": "application/zip"},
    )
    assert response.status_code == 413
    assert not list((app.state.database.root / "jobs").glob(".restore-*"))
    response = upload(client, data=b"x" * (8 * 1024 * 1024 + 65536))
    assert response.status_code == 413
    with app.state.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM recipe_media").fetchone()[0] == 0
