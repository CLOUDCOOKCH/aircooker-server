import json
from uuid import uuid4

import pytest

from aircooker.errors import DomainError
from aircooker.importing import extract, platform_for, public_addresses
from aircooker.jobs import claim, finish


def test_structured_extraction_preserves_unparsed_ingredients():
    source = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": "Soup",
        "recipeIngredient": ["salt to taste", "200 g carrots"],
        "recipeInstructions": [{"@type": "HowToStep", "text": "Cook"}],
        "recipeYield": "2",
    }
    recipe, warnings = extract(
        '<script type="application/ld+json">' + json.dumps(source) + "</script>"
    )
    assert recipe.title == "Soup" and recipe.steps == ["Cook"]
    assert recipe.ingredients[1].original_text == "200 g carrots"
    assert recipe.ingredients[1].quantity is None
    assert warnings


def test_import_requires_explicit_confirmation(harness, mutation):
    c, app, device, tokens = harness
    source = json.dumps(
        {
            "@type": "Recipe",
            "name": "Soup",
            "recipeIngredient": ["salt"],
            "recipeInstructions": ["Cook"],
        }
    )
    response = c.post("/api/v1/imports", json={"text": source})
    assert response.status_code == 202
    job = claim(app.state.database)
    app.state.process_job(job)
    finish(app.state.database, job)
    draft = c.get("/api/v1/imports/" + response.json()["id"]).json()
    assert draft["state"] == "preview"
    assert c.get("/api/v1/recipes").json()["items"] == []
    m = mutation(device, payload=draft["recipe"])
    assert c.post("/api/v1/imports/" + draft["id"] + "/confirm", json=m).status_code == 200
    assert len(c.get("/api/v1/recipes").json()["items"]) == 1


def test_private_dns_and_mixed_answers_rejected(monkeypatch):
    for addresses in [
        ["127.0.0.1"],
        ["169.254.169.254"],
        ["10.1.1.1"],
        ["::1"],
        ["93.184.216.34", "192.168.1.1"],
    ]:
        monkeypatch.setattr(
            "socket.getaddrinfo",
            lambda *a, **k: [(2, 1, 6, "", (address, 443)) for address in addresses],
        )
        with pytest.raises(DomainError, match="source_address_forbidden"):
            public_addresses("example.test", 443)


def test_platform_matching_and_no_fabrication():
    assert platform_for("https://notinstagram.com/a") == "website"
    assert platform_for("https://www.instagram.com/p/a") == "instagram"
    with pytest.raises(DomainError, match="structured_recipe_not_found"):
        extract("a video caption without a recipe")


def test_bounded_fetch_rejects_non_https_without_network():
    from aircooker.importing import bounded_fetch_html

    with pytest.raises(DomainError, match="source_url_forbidden"):
        bounded_fetch_html("http://127.0.0.1:8000/private")


def test_import_request_id_replays_and_rejects_changed_content(harness):
    c, app, device, tokens = harness
    body = {"request_id": str(uuid4()), "text": '{"@type":"Recipe","name":"Soup"}'}
    first = c.post("/api/v1/imports", json=body)
    assert first.status_code == 202
    assert c.post("/api/v1/imports", json=body).json() == first.json()
    assert c.post("/api/v1/imports", json={**body, "text": "changed"}).status_code == 409


def test_multicast_and_ipv6_transition_addresses_are_not_public_sources():
    from aircooker.importing import public_address

    for address in ["224.0.0.1", "ff02::1", "2002:7f00:1::", "::ffff:127.0.0.1", "240.0.0.1"]:
        assert not public_address(address)
    assert public_address("93.184.216.34")
