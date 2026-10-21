"""Real local OCR, durable import previews and review-only confirmation."""

import io
import json
import subprocess
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from PIL import Image

from aircooker.ai import provider_for
from aircooker.ai_settings import AISettings, save_configuration
from aircooker.db import Database
from aircooker.errors import DomainError
from aircooker.image_import import ocr_available, printed_recipe, recognise_text
from aircooker.import_receipts import fingerprint
from aircooker.jobs import claim, finish
from aircooker.retention import DAY, cleanup_database

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    "language,title,count,servings", [("en", "Lemon rice", 3, 4), ("de", "Tomatenreis", 2, 2)]
)
def test_real_ocr_and_recipe_sections(language, title, count, servings):
    assert ocr_available(), (
        "Install Tesseract with eng and deu language data; real OCR is mandatory"
    )
    text = recognise_text((FIXTURES / f"recipe-photo-{language}.png").read_bytes())
    recipe, warnings = printed_recipe(text, uuid4())
    assert recipe.title == title
    assert len(recipe.ingredients) == 3
    assert recipe.ingredients[0].quantity == 200
    assert recipe.ingredients[0].unit == "g"
    assert recipe.servings == servings
    assert len(recipe.steps) == count
    assert recipe.nutrition is None
    assert "image_text_requires_review" in warnings


def test_blank_photo_does_not_fabricate_recipe():
    output = io.BytesIO()
    Image.new("RGB", (200, 200), "white").save(output, "JPEG")
    with pytest.raises(DomainError, match="image_no_readable_text"):
        recognise_text(output.getvalue())


def test_unclear_recipe_preserves_facts_without_guessing():
    with pytest.raises(DomainError, match="image_recipe_layout_unclear"):
        printed_recipe("A beautiful plate of rice", uuid4())
    recipe, warnings = printed_recipe(
        "Rice\nIngredients\nSalt to taste\nInstructions\nMix gently.", uuid4()
    )
    assert recipe.ingredients[0].quantity is None
    assert recipe.ingredients[0].original_text == "Salt to taste"
    assert recipe.provenance["servings"] == "default_requires_review"
    assert recipe.nutrition is None


def test_ocr_process_is_bounded_and_does_not_receive_secrets(monkeypatch):
    assert ocr_available()
    monkeypatch.setenv("AI_API_KEY", "synthetic-never-forward-this")

    def timeout(args, **kwargs):
        assert "AI_API_KEY" not in kwargs["env"]
        assert kwargs["env"]["OMP_THREAD_LIMIT"] == "1"
        assert kwargs["timeout"] == 20
        assert "shell" not in kwargs
        raise subprocess.TimeoutExpired(args, 20)

    monkeypatch.setattr("aircooker.image_import.subprocess.run", timeout)
    with pytest.raises(DomainError, match="image_ocr_timeout"):
        recognise_text(b"validated-image-placeholder")


def test_oversized_ocr_output_rejected(monkeypatch):
    assert ocr_available()

    def output(args, **kwargs):
        kwargs["stdout"].write(b"a" * 100001)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr("aircooker.image_import.subprocess.run", output)
    with pytest.raises(DomainError, match="image_text_too_large"):
        recognise_text(b"validated-image-placeholder")


def test_missing_engine_is_explicit(monkeypatch):
    ocr_available.cache_clear()
    try:
        monkeypatch.setattr("aircooker.image_import.shutil.which", lambda name: None)
        with pytest.raises(DomainError, match="image_ocr_unavailable"):
            recognise_text(b"image")
    finally:
        ocr_available.cache_clear()


def upload(client, language="en"):
    image_id = str(uuid4())
    response = client.put(
        "/api/v1/media/" + image_id,
        files={
            "file": (
                "recipe.png",
                (FIXTURES / f"recipe-photo-{language}.png").read_bytes(),
                "image/png",
            )
        },
    )
    assert response.status_code == 200, response.text
    return image_id


def process(app):
    job = claim(app.state.database)
    assert job and job["kind"] == "recipe.import"
    app.state.process_job(job)
    finish(app.state.database, job)


def test_image_import_survives_restart_and_requires_review(harness, mutation):
    client, app, device, tokens = harness
    image_id = upload(client)
    body = {"request_id": str(uuid4()), "image_id": image_id}
    response = client.post("/api/v1/imports", json=body)
    assert response.status_code == 202, response.text
    # Migration/startup is repeatable while queued work and the image remain durable.
    reopened = Database(app.state.database.root)
    with reopened.connect() as db:
        assert (
            db.execute(
                "SELECT image_id FROM (SELECT json_extract(payload,'$.image_id') AS image_id FROM background_job WHERE kind='recipe.import')"
            ).fetchone()[0]
            == image_id
        )
    process(app)
    draft = client.get("/api/v1/imports/" + body["request_id"]).json()
    assert draft["state"] == "preview", draft
    assert "Lemon rice" in draft["recognized_text"]
    assert draft["recipe"]["image_id"] == image_id
    assert draft["recipe"]["source_platform"] == "image"
    assert client.get("/api/v1/recipes").json()["items"] == []
    draft["recipe"]["title"] = "Reviewed lemon rice"
    confirmation = mutation(device, payload=draft["recipe"])
    result = client.post("/api/v1/imports/" + draft["id"] + "/confirm", json=confirmation)
    assert result.status_code == 200, result.text
    assert (
        client.get("/api/v1/recipes/" + confirmation["entity_id"]).json()["payload"]["title"]
        == "Reviewed lemon rice"
    )
    with app.state.database.connect() as db:
        finished = db.execute(
            "SELECT finished_at FROM import_draft WHERE id=?", (draft["id"],)
        ).fetchone()[0]
    cleanup_database(app.state.database, now=finished + 31 * DAY)
    assert client.get("/api/v1/imports/" + draft["id"]).json()["recognized_text"] is None
    assert client.post("/api/v1/imports", json=body).json()["state"] == "confirmed"


def test_image_receipt_deduplicates_retries_and_detects_changed_image(harness):
    client, app, device, tokens = harness
    image_id = upload(client)
    body = {"request_id": str(uuid4()), "image_id": image_id}
    first = client.post("/api/v1/imports", json=body)
    for _ in range(25):
        assert client.post("/api/v1/imports", json=body).json() == first.json()
    assert (
        client.post("/api/v1/imports", json={**body, "image_id": str(uuid4())}).status_code == 409
    )
    with app.state.database.connect() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM background_job WHERE kind='recipe.import'").fetchone()[
                0
            ]
            == 1
        )


def test_invalid_image_reference_and_no_premature_confirmation(harness, mutation):
    client, app, device, tokens = harness
    assert client.post("/api/v1/imports", json={"image_id": str(uuid4())}).status_code == 404
    response = client.post("/api/v1/imports", json={"image_id": upload(client)})
    assert (
        client.post(
            "/api/v1/imports/" + response.json()["id"] + "/confirm", json=mutation(device)
        ).status_code
        == 409
    )
    assert client.delete("/api/v1/imports/" + response.json()["id"]).status_code == 204
    process(app)
    assert client.get("/api/v1/imports/" + response.json()["id"]).json()["state"] == "cancelled"
    assert not client.get("/api/v1/recipes").json()["items"]


def test_failed_extraction_retains_recognized_text_for_correction(harness, monkeypatch):
    client, app, device, tokens = harness
    monkeypatch.setattr(
        "aircooker.app.recognise_text", lambda data: "Rice with tomatoes. No headings."
    )
    result = client.post("/api/v1/imports", json={"image_id": upload(client)})
    process(app)
    draft = client.get("/api/v1/imports/" + result.json()["id"]).json()
    assert draft["state"] == "needs_input"
    assert draft["error_code"] == "image_recipe_layout_unclear"
    assert draft["recognized_text"] == "Rice with tomatoes. No headings."
    assert draft["recipe"] is None


def test_corrected_text_skips_ocr_and_optional_ai_keeps_disclosure(harness, monkeypatch):
    client, app, device, tokens = harness

    def never(data):
        raise AssertionError("Corrected text should not be overwritten by another OCR run")

    monkeypatch.setattr("aircooker.app.recognise_text", never)
    image_id = upload(client)
    text = "Edited rice\nIngredients\n200 g rice\nInstructions\nCook the rice."
    result = client.post(
        "/api/v1/imports", json={"image_id": image_id, "text": text, "use_ai": True}
    )
    process(app)
    draft = client.get("/api/v1/imports/" + result.json()["id"]).json()
    assert draft["error_code"] == "ai_not_configured"
    assert draft["recognized_text"] == text
    result = client.post("/api/v1/imports", json={"image_id": image_id, "text": text})
    process(app)
    assert (
        client.get("/api/v1/imports/" + result.json()["id"]).json()["recipe"]["title"]
        == "Edited rice"
    )


def test_old_text_import_fingerprints_remain_unchanged():
    import hashlib

    values = {
        "text": "legacy source",
        "source_url": None,
        "use_ai": False,
        "consent_external_ai": False,
    }
    original = hashlib.sha256(
        json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert fingerprint({**values, "image_id": None}) == original


def test_image_ai_requires_consent_and_sends_only_recognized_text(harness, monkeypatch):
    client, app, device, tokens = harness
    save_configuration(
        app.state.database.root / "config",
        AISettings(provider="openai-compatible", base_url="https://ai.example/v1", model="test"),
    )
    sent = []

    def handle(request):
        body = json.loads(request.content)
        sent.append(body)
        assert request.url.path == "/v1/chat/completions"
        assert all(isinstance(message["content"], str) for message in body["messages"])
        source = json.loads(body["messages"][1]["content"])
        assert set(source) == {"untrusted_source"}
        assert "Lemon rice" in source["untrusted_source"]
        assert "200 g rice" in source["untrusted_source"]
        assert "data:image" not in request.content.decode()
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(
                                {
                                    "title": "Lemon rice",
                                    "servings": "4",
                                    "ingredients": [
                                        {
                                            "id": str(uuid4()),
                                            "name": "rice",
                                            "quantity": "200",
                                            "unit": "g",
                                        }
                                    ],
                                    "steps": ["Cook the rice."],
                                }
                            )
                        },
                    }
                ]
            },
        )

    monkeypatch.setattr(
        "aircooker.app.provider_for",
        lambda config: provider_for(config, httpx.MockTransport(handle)),
    )
    image_id = upload(client)
    unconsented = client.post("/api/v1/imports", json={"image_id": image_id, "use_ai": True})
    process(app)
    blocked = client.get("/api/v1/imports/" + unconsented.json()["id"]).json()
    assert blocked["error_code"] == "ai_content_disclosure_consent_required"
    assert "Lemon rice" in blocked["recognized_text"]
    assert sent == []
    allowed = client.post(
        "/api/v1/imports",
        json={
            "image_id": image_id,
            "use_ai": True,
            "consent_external_ai": True,
        },
    )
    process(app)
    draft = client.get("/api/v1/imports/" + allowed.json()["id"]).json()
    assert draft["state"] == "preview", draft
    assert len(sent) == 1
    assert draft["recipe"]["image_id"] == image_id
    assert draft["recipe"]["provenance"]["input"] == "local-image-ocr"
    assert client.get("/api/v1/recipes").json()["items"] == []
