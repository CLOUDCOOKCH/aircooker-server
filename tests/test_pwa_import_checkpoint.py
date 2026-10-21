import json


def test_import_confirmation_checks_history_proof_before_any_write(harness, mutation):
    client, app, device, _ = harness
    source = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": "Carrot soup",
        "recipeYield": "2",
        "recipeIngredient": ["200 g carrots"],
        "recipeInstructions": ["Simmer the carrots."],
    }
    created = client.post(
        "/api/v1/imports",
        json={"text": '<script type="application/ld+json">' + json.dumps(source) + "</script>"},
    )
    assert created.status_code == 202
    iid = created.json()["id"]
    with app.state.database.connect() as db:
        job = dict(db.execute("SELECT * FROM background_job WHERE kind='recipe.import'").fetchone())
    app.state.process_job(job)
    preview = client.get("/api/v1/imports/" + iid).json()
    assert preview["state"] == "preview"
    body = mutation(device, payload=preview["recipe"])
    url = "/api/v1/imports/" + iid + "/confirm"
    response = client.post(
        url, json=body, headers={"X-Aircooker-Sync-Cursor": "0", "X-Aircooker-Sync-Token": "a" * 32}
    )
    assert (
        response.status_code == 409 and response.json()["error"]["code"] == "sync_history_changed"
    )
    assert client.post(url, json=body, headers={"X-Aircooker-Sync-Cursor": "0"}).status_code == 422
    assert client.get("/api/v1/recipes").json()["items"] == []
    assert client.get("/api/v1/imports/" + iid).json()["state"] == "preview"
    confirmed = client.post(
        url, json=body, headers={"X-Aircooker-Sync-Cursor": "0", "X-Aircooker-Sync-Token": "root"}
    )
    assert confirmed.status_code == 200 and confirmed.json()["status"] == "accepted"
    replay = client.post(
        url, json=body, headers={"X-Aircooker-Sync-Cursor": "0", "X-Aircooker-Sync-Token": "root"}
    )
    assert replay.json() == confirmed.json()
    assert len(client.get("/api/v1/recipes").json()["items"]) == 1
