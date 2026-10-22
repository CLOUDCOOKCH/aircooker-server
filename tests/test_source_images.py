import io
import json
import time
from pathlib import Path

import pytest
from PIL import Image

from aircooker.errors import DomainError
from aircooker.importing import FetchedPage, extract, fetch_page, fetch_resource, public_addresses
from aircooker.jobs import claim, finish
from aircooker.media import normalise_image
from aircooker.recipe_extraction import ExtractionResult
from aircooker.retention import DAY, cleanup_database
from aircooker.source_images import bounded_source_photo, image_candidates, source_photo


def picture():
    output = io.BytesIO()
    image = Image.new("RGB", (80, 60), "coral")
    exif = Image.Exif()
    exif[270] = "Synthetic metadata must not survive"
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


def metadata():
    return json.dumps(
        {
            "@type": "Recipe",
            "name": "Source soup",
            "image": {"url": "photos/soup.jpg"},
            "recipeIngredient": ["200 g carrots"],
            "recipeInstructions": ["Cook"],
            "recipeYield": "2",
        }
    )


def test_schema_image_objects_and_arrays_precede_page_previews_and_resolve_final_page_url():
    page = FetchedPage(
        '<meta property="og:image" content="/preview.jpg"><meta name="twitter:image" content="/social.jpg">'
        '<script type="application/ld+json">'
        + json.dumps(
            {
                "@graph": [
                    {
                        "@type": "Recipe",
                        "image": [
                            {"contentUrl": "food.jpg"},
                            "https://cdn.example.org/dish.png",
                            "food.jpg",
                        ],
                    }
                ]
            }
        )
        + "</script>",
        "https://example.org/redirected/recipe/",
    )
    assert image_candidates(page) == [
        "https://example.org/redirected/recipe/food.jpg",
        "https://cdn.example.org/dish.png",
        "https://example.org/preview.jpg",
    ]


def test_invalid_metadata_never_becomes_an_arbitrary_image_or_script():
    page = FetchedPage(
        '<script type="application/ld+json">broken</script>'
        '<meta property="og:image" content="data:image/png;base64,AAAA">'
        '<meta property="og:image" content="https://user:pass@example.org/a.jpg">'
        '<meta property="og:image" content="http://example.org/a.jpg">'
        '<meta property="og:image" content="https://example.org:444/a.jpg">'
        '<img src="https://example.org/tracking.jpg"><meta name="twitter:image" content="/dish.jpg">',
        "https://example.org/recipe",
    )
    assert image_candidates(page) == ["https://example.org/dish.jpg"]


def test_photo_download_rejects_bad_first_candidate_and_strips_metadata(monkeypatch):
    page = FetchedPage(
        '<meta property="og:image" content="/bad.svg">'
        '<meta name="twitter:image" content="/dish.jpg">',
        "https://example.org/r",
    )
    calls = []

    def download(url, content_types, max_bytes):
        calls.append(url)
        assert "image/svg+xml" not in content_types and max_bytes == 8 * 1024 * 1024
        if url.endswith(".svg"):
            raise DomainError("source_content_type_unsupported", 422)
        return picture(), "image/jpeg", url

    monkeypatch.setattr("aircooker.source_images.fetch_resource", download)
    data, width, height, origin = source_photo(page.url, page)
    assert len(calls) == 2 and origin.endswith("/dish.jpg") and (width, height) == (80, 60)
    with Image.open(io.BytesIO(data)) as image:
        assert image.format == "JPEG" and not image.getexif()


class Response:
    def __init__(self, status, headers, body=b""):
        self.status, self.headers, self.body = status, headers, body

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def read(self, size):
        return self.body[:size]


def transport(monkeypatch, responses):
    calls = []
    monkeypatch.setattr(
        "aircooker.importing.public_addresses", lambda host, port: ["93.184.216.34"]
    )

    class Connection:
        def __init__(self, host, address):
            assert address == "93.184.216.34"
            self.host = host

        def request(self, method, path, headers):
            assert headers["Accept-Encoding"] == "identity"
            assert "Authorization" not in headers and "Cookie" not in headers
            calls.append((self.host, path))

        def getresponse(self):
            return responses.pop(0)

        def close(self):
            pass

    monkeypatch.setattr("aircooker.importing.PinnedHTTPS", Connection)
    return calls


def test_redirected_page_carries_actual_base_for_relative_photos(monkeypatch):
    calls = transport(
        monkeypatch,
        [
            Response(302, {"Location": "/new/recipe/"}),
            Response(
                200, {"Content-Type": "text/html"}, b'<meta property="og:image" content="dish.jpg">'
            ),
        ],
    )
    page = fetch_page("https://example.org/old")
    assert page.url == "https://example.org/new/recipe/"
    assert image_candidates(page) == ["https://example.org/new/recipe/dish.jpg"]
    assert calls == [("example.org", "/old"), ("example.org", "/new/recipe/")]


def test_image_redirect_to_private_or_mixed_dns_is_rejected_before_connection(monkeypatch):
    calls = transport(monkeypatch, [Response(302, {"Location": "https://127.0.0.1/secret"})])
    monkeypatch.setattr("aircooker.importing.public_addresses", public_addresses)
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda host, *a, **kw: [
            (2, 1, 6, "", ("127.0.0.1" if host == "127.0.0.1" else "93.184.216.34", 443))
        ],
    )
    with pytest.raises(DomainError, match="source_address_forbidden"):
        fetch_resource("https://example.org/image", {"image/jpeg"}, 1024)
    assert calls == [("example.org", "/image")]


@pytest.mark.parametrize(
    "response",
    [
        Response(200, {"Content-Type": "image/svg+xml"}, b"<svg/>"),
        Response(200, {"Content-Type": "image/jpeg", "Content-Encoding": "gzip"}, b"bad"),
        Response(200, {"Content-Type": "image/jpeg"}, b"too many bytes"),
        Response(403, {"Content-Type": "text/html"}, b"login required"),
    ],
)
def test_download_content_type_encoding_size_and_access_limits(monkeypatch, response):
    transport(monkeypatch, [response])
    with pytest.raises(DomainError):
        fetch_resource("https://example.org/a", {"image/jpeg"}, 5)


def test_isolated_photo_fetch_fails_safely_without_any_network_for_http_source():
    assert bounded_source_photo("http://127.0.0.1/private", None) is None


@pytest.mark.parametrize("ai_state", ["metadata", "complete", "partial"])
def test_source_photo_is_reviewed_saved_and_replay_safe(harness, mutation, monkeypatch, ai_state):
    client, app, device, _ = harness
    use_ai = ai_state != "metadata"
    url = "https://example.org/recipes/soup/"
    content = '<meta property="og:image" content="photo.jpg">' if use_ai else metadata()
    monkeypatch.setattr(
        "aircooker.app.bounded_fetch_page", lambda source: FetchedPage(content, url)
    )
    monkeypatch.setattr(
        "aircooker.source_images.fetch_resource",
        lambda *args: (picture(), "image/jpeg", url + "photo.jpg"),
    )
    calls = []

    def photo(source, page):
        calls.append((source, page.url))
        return source_photo(source, page)

    monkeypatch.setattr("aircooker.app.bounded_source_photo", photo)
    if use_ai:
        client.put(
            "/api/v1/admin/ai",
            json={
                "provider": "gemini",
                "model": "synthetic-model",
                "api_key": "synthetic-key",
                "input_formats": ["text"],
            },
        ).raise_for_status()

        class Provider:
            def extract(self, value):
                result = json.loads(
                    Path("contracts/recipe-import/examples/extraction-result.json").read_text()
                )
                if ai_state == "partial":
                    result["recipe"]["servings"] = None
                return ExtractionResult.model_validate(result)

            def close(self):
                pass

        monkeypatch.setattr("aircooker.app.provider_for", lambda config: Provider())
    queued = client.post(
        "/api/v1/imports", json={"source_url": url, "use_ai": use_ai, "consent_external_ai": use_ai}
    ).json()
    job = claim(app.state.database)
    app.state.process_job(job)
    app.state.process_job(job)  # Crash after saving the preview, before acknowledging the job.
    finish(app.state.database, job)
    draft = client.get("/api/v1/imports/" + queued["id"]).json()
    assert draft["state"] == "preview" and draft["source_photo"]["image_id"] and len(calls) == 1
    assert draft["source_photo"]["source_url"] == url + "photo.jpg"
    if ai_state == "partial":
        assert draft["recipe"] is None and draft["extraction"]["recipe"]["servings"] is None
        reviewed = extract(metadata(), url)[0].model_dump(mode="json")
        reviewed["image_id"] = draft["source_photo"]["image_id"]
    else:
        reviewed = draft["recipe"]
        assert reviewed["provenance"]["image_source"] == url + "photo.jpg"
    assert "source_image_unavailable" not in draft["warnings"]
    assert client.get("/api/v1/recipes").json()["items"] == []
    photo_response = client.get("/api/v1/media/" + draft["source_photo"]["image_id"])
    assert (
        photo_response.status_code == 200 and photo_response.headers["content-type"] == "image/jpeg"
    )
    saved = client.post(
        "/api/v1/imports/" + draft["id"] + "/confirm", json=mutation(device, payload=reviewed)
    )
    assert saved.status_code == 200
    assert (
        client.get("/api/v1/recipes").json()["items"][0]["payload"]["image_id"]
        == draft["source_photo"]["image_id"]
    )
    cleanup_database(app.state.database, now=time.time() + 31 * DAY)
    retained = client.get("/api/v1/imports/" + draft["id"]).json()
    assert retained["state"] == "confirmed" and retained["source_photo"] is None
    assert client.get("/api/v1/media/" + reviewed["image_id"]).status_code == 200


@pytest.mark.parametrize("failure", ["missing", "blocked", "quota", "cancelled"])
def test_photo_failure_or_cancellation_does_not_save_a_recipe_or_orphan_media(
    harness, monkeypatch, failure
):
    client, app, _, _ = harness
    url = "https://example.org/recipe"
    monkeypatch.setattr(
        "aircooker.app.bounded_fetch_page", lambda source: FetchedPage(metadata(), url)
    )
    queued = client.post("/api/v1/imports", json={"source_url": url}).json()

    def photo(*args):
        if failure == "blocked":
            raise DomainError("source_address_forbidden", 422)
        if failure == "missing":
            return None
        if failure == "cancelled":
            with app.state.database.transaction() as db:
                db.execute("UPDATE import_draft SET state='cancelled' WHERE id=?", (queued["id"],))
        data, width, height = normalise_image(picture(), "image/jpeg")
        return data, width, height, url + "/photo.jpg"

    monkeypatch.setattr("aircooker.app.bounded_source_photo", photo)
    if failure == "quota":

        def no_space(*args):
            raise DomainError("media_storage_limit", 409)

        monkeypatch.setattr("aircooker.recipe_imports.insert_media", no_space)
    job = claim(app.state.database)
    app.state.process_job(job)
    finish(app.state.database, job)
    draft = client.get("/api/v1/imports/" + queued["id"]).json()
    if failure == "cancelled":
        assert draft["state"] == "cancelled"
    else:
        assert draft["state"] == "preview" and draft["recipe"]["image_id"] is None
        assert "source_image_unavailable" in draft["warnings"]
    with app.state.database.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM recipe_media").fetchone()[0] == 0
    assert client.get("/api/v1/recipes").json()["items"] == []
