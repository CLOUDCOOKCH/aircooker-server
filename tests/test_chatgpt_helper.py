"""Exercise the standalone helper's real loopback listener with synthetic OAuth responses."""

import base64
import hashlib
import http.client
import threading
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest

from mealf.chatgpt_helper import (
    AUTH,
    PREFIX,
    RESOURCE,
    TOKEN,
    ConnectError,
    connect,
    local_host_id,
    server_origin,
)


def test_real_loopback_pkce_callback_and_protected_transfer(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert local_host_id() == local_host_id()
    calls, browser_requests, callbacks = [], [], []
    pair_code = "synthetic_pairing_capability_123456789"

    def request(url, body=None, *, form=False):
        calls.append((url, body, form))
        if url.endswith("/pairing/claim"):
            return {
                "nonce": "synthetic-nonce",
                "client_id": "dynamic_agent_client",
                "host_id": "urn:uuid:remote-host",
            }
        if url.endswith("/.well-known/openid-configuration"):
            return {
                "issuer": AUTH,
                "authorization_endpoint": AUTH + "/api/accounts/authorize",
                "token_endpoint": TOKEN,
            }
        if url == TOKEN:
            assert form is True and body["resource"] == RESOURCE
            query = browser_requests[0]
            challenge = (
                base64.urlsafe_b64encode(hashlib.sha256(body["code_verifier"].encode()).digest())
                .decode()
                .rstrip("=")
            )
            assert challenge == query["code_challenge"][0]
            assert body["redirect_uri"] == query["redirect_uri"][0]
            assert body["client_id"] == "oaiapp_synthetic"
            return {
                "access_token": "synthetic-access",
                "refresh_token": "synthetic-refresh",
                "id_token": "synthetic-id",
                "token_type": "Bearer",
                "scope": "synthetic-scopes",
                "expires_in": 3600,
                "ignore_unknown_field": "not transferred",
            }
        assert url == "https://mealf.example" + PREFIX + "/pairing/complete"
        assert body["code"] == pair_code and body["client_id"] == "oaiapp_synthetic"
        assert "ignore_unknown_field" not in body["tokens"]
        return {"state": "connected"}

    def browser(url):
        parsed = urlsplit(url)
        assert parsed.scheme == "https" and parsed.netloc == "auth.openai.com"
        query = parse_qs(parsed.query)
        browser_requests.append(query)
        assert query["agent_name_hint"] == ["mealf"]
        assert query["nonce"] == ["synthetic-nonce"]
        assert query["code_challenge_method"] == ["S256"]
        callback = urlsplit(query["redirect_uri"][0])
        assert callback.hostname == "127.0.0.1" and callback.path == "/auth/callback"

        def send():
            connection = http.client.HTTPConnection("127.0.0.1", callback.port, timeout=5)
            # A wrong state cannot consume the legitimate authorization attempt.
            connection.request(
                "GET", callback.path + "?" + urlencode({"state": "wrong", "code": "bad"})
            )
            response = connection.getresponse()
            assert response.status == 400
            response.read()
            connection.close()
            connection = http.client.HTTPConnection("127.0.0.1", callback.port, timeout=5)
            connection.request(
                "GET",
                callback.path
                + "?"
                + urlencode(
                    {
                        "state": query["state"][0],
                        "code": "synthetic-code",
                        "client_id": "oaiapp_synthetic",
                    }
                ),
            )
            response = connection.getresponse()
            assert response.status == 200 and response.getheader("Cache-Control") == "no-store"
            response.read()
            connection.close()

        thread = threading.Thread(target=send)
        thread.start()
        callbacks.append(thread)
        return True

    result = connect("https://mealf.example", pair_code, request=request, open_browser=browser)
    for thread in callbacks:
        thread.join(timeout=5)
        assert not thread.is_alive()
    assert result["state"] == "connected"
    files = list(tmp_path.rglob("*"))
    for path in files:
        if path.is_file():
            assert (
                "synthetic-access" not in path.read_text()
                and "synthetic-refresh" not in path.read_text()
            )
    assert len(calls) == 4


@pytest.mark.parametrize(
    "value",
    [
        "http://mealf.example",
        "https://user:password@mealf.example",
        "https://mealf.example/?token=secret",
        "https://mealf.example/path",
        "https://mealf.example/#x",
        "https://mealf.example:bad",
    ],
)
def test_helper_requires_https_origin_and_keeps_credentials_out_of_url(value):
    with pytest.raises(ConnectError):
        server_origin(value)


def test_callback_browser_failure_has_no_credential_dump():
    def request(url, body=None):
        if url.endswith("/claim"):
            return {
                "nonce": "synthetic",
                "client_id": "oaiapp_returning",
                "id_token_hint": "private-synthetic-hint",
            }
        return {
            "issuer": AUTH,
            "authorization_endpoint": AUTH + "/api/accounts/authorize",
            "token_endpoint": TOKEN,
        }

    with pytest.raises(ConnectError, match="browser_unavailable") as error:
        connect(
            "https://mealf.example",
            "synthetic_pairing_capability_123456789",
            request=request,
            open_browser=lambda url: False,
            host=lambda: "urn:uuid:local",
        )
    assert "private-synthetic-hint" not in str(error.value)
