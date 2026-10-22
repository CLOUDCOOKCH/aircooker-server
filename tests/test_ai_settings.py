import pytest

from mealf.ai_settings import load_configuration


def configuration(**changes):
    return {
        "provider": "openai-compatible",
        "base_url": "https://ai.example/v1",
        "model": "test-model",
        **changes,
    }


def test_gemini_requires_api_identifier_instead_of_display_name(harness):
    c, _, *_ = harness
    response = c.put(
        "/api/v1/admin/ai",
        json=configuration(provider="gemini", model="Gemini 3.8 Flash"),
    )
    assert response.status_code == 422
    assert response.json() == {"error": {"code": "invalid_gemini_model_id"}}
    assert not c.get("/api/v1/admin/ai").json()["enabled"]
    for model in ("gemini-3.8-flash", "models/gemini-3.8-flash"):
        response = c.put("/api/v1/admin/ai", json=configuration(provider="gemini", model=model))
        assert response.status_code == 200 and response.json()["model"] == model


def test_saved_ai_settings_are_encrypted_and_never_return_keys(harness):
    c, app, _, _ = harness
    secret = "synthetic AI credential for test only"
    response = c.put("/api/v1/admin/ai", json=configuration(api_key=secret))
    assert response.status_code == 200 and response.json()["key_configured"]
    assert secret not in response.text and "api_key" not in response.json()
    assert secret not in c.get("/api/v1/admin/ai").text
    root = app.state.database.root / "config"
    assert secret.encode() not in (root / "ai-provider.enc").read_bytes()
    assert load_configuration(root).api_key == secret
    assert c.get("/api/v1/system/capabilities").json()["ai"]
    exported = c.get("/api/v1/admin/export")
    assert secret not in exported.text


def test_key_retention_is_bound_to_endpoint_and_provider(harness):
    c, app, _, _ = harness
    root = app.state.database.root / "config"
    c.put("/api/v1/admin/ai", json=configuration(api_key="synthetic test credential"))
    assert c.put("/api/v1/admin/ai", json=configuration(model="other-model")).json()[
        "key_configured"
    ]
    assert not c.put(
        "/api/v1/admin/ai", json=configuration(base_url="https://other.example/v1")
    ).json()["key_configured"]
    assert load_configuration(root).api_key == ""


def test_disabled_saved_settings_override_environment(harness, monkeypatch):
    c, app, _, _ = harness
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_MODEL", "test")
    assert c.get("/api/v1/admin/ai").json()["origin"] == "environment"
    assert c.put("/api/v1/admin/ai", json={"enabled": False}).status_code == 200
    assert load_configuration(app.state.database.root / "config") is None
    assert not c.get("/api/v1/system/capabilities").json()["ai"]
    assert c.post("/api/v1/admin/ai/test").status_code == 409


def test_ai_admin_validation_authentication_and_probe(harness, monkeypatch):
    c, _, _, _ = harness
    assert (
        c.put("/api/v1/admin/ai", json=configuration(base_url="http://localhost:11434")).status_code
        == 422
    )
    assert c.put("/api/v1/admin/ai", json=configuration(timeout=121)).status_code == 422
    assert c.put("/api/v1/admin/ai", json=configuration()).status_code == 200
    probes = []

    class Provider:
        def extract_recipe(self, content):
            probes.append(content)

        def close(self):
            pass

    monkeypatch.setattr("mealf.app.provider_for", lambda config: Provider())
    response = c.post("/api/v1/admin/ai/test")
    assert response.status_code == 200 and response.json()["household_content_sent"] is False
    assert len(probes) == 1 and "Connection test soup" in probes[0]
    for _ in range(4):
        assert c.post("/api/v1/admin/ai/test").status_code == 200
    assert c.post("/api/v1/admin/ai/test").status_code == 429
    c.headers.pop("Authorization")
    assert c.get("/api/v1/admin/ai").status_code == 401
    assert c.put("/api/v1/admin/ai", json=configuration()).status_code == 401


@pytest.mark.parametrize(
    "bad", [{"AI_TIMEOUT": "invalid"}, {"AI_API_KEY_FILE": "/nonexistent/mealf-synthetic-key"}]
)
def test_invalid_environment_can_be_repaired_without_exposing_values(harness, monkeypatch, bad):
    c, _, _, _ = harness
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_MODEL", "test")
    for key, value in bad.items():
        monkeypatch.setenv(key, value)
    status = c.get("/api/v1/admin/ai")
    assert status.status_code == 200 and status.json()["configuration_error"]
    assert not c.get("/api/v1/system/capabilities").json()["ai"]
    assert (
        c.put(
            "/api/v1/admin/ai", json=configuration(api_key="synthetic repair credential")
        ).status_code
        == 200
    )
    assert c.get("/api/v1/admin/ai").json()["enabled"]


def test_status_and_session_inventory_are_protected_and_redacted(harness):
    c, _, _, tokens = harness
    data = c.get("/api/v1/admin/status").json()
    assert data["database_bytes"] > 0 and data["media_bytes"] == 0 and data["disk_free_bytes"] > 0
    sessions = c.get("/api/v1/auth/sessions").json()
    assert [s["id"] for s in sessions if s["current"]] == [tokens["session_id"]]
    assert "access_token" not in str(sessions) and "password" not in str(data)
    c.headers.pop("Authorization")
    assert c.get("/api/v1/admin/status").status_code == 401


def test_malformed_ai_key_is_rejected_without_echoing_it(harness):
    c, _, _, _ = harness
    secret = "synthetic private credential\nwith control data"
    result = c.put("/api/v1/admin/ai", json=configuration(api_key=secret))
    assert result.status_code == 422 and result.json()["error"]["code"] == "invalid_ai_key"
    assert "synthetic private" not in result.text


def test_connection_probe_obeys_configured_hourly_budget(harness, monkeypatch):
    c, _, _, _ = harness
    assert c.put("/api/v1/admin/ai", json=configuration(requests_per_hour=1)).status_code == 200
    probes = []

    class Provider:
        def extract_recipe(self, content):
            probes.append(content)

        def close(self):
            pass

    monkeypatch.setattr("mealf.app.provider_for", lambda config: Provider())
    assert c.post("/api/v1/admin/ai/test").status_code == 200
    assert c.post("/api/v1/admin/ai/test").status_code == 429
    assert len(probes) == 1
