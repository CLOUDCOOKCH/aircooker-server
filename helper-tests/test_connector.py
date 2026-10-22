"""Platform acceptance for the downloaded file, without installing the server or packages."""

import base64
import hashlib
import http.client
import json
import os
import runpy
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

helper = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "src/aircooker/chatgpt_helper.py")
)


class StandaloneConnector(unittest.TestCase):
    def test_callback_pkce_transfer_and_no_local_credentials(self):
        calls, parameters, threads, thread_errors = [], {}, [], []
        origin = "https://mealf.example"

        def request(url, body=None, *, form=False):
            calls.append(url)
            if url == origin + helper["PREFIX"] + "/pairing/claim":
                return {"nonce": "synthetic-nonce", "client_id": "dynamic_agent_client"}
            if url.endswith("/.well-known/openid-configuration"):
                return {
                    "issuer": helper["AUTH"],
                    "authorization_endpoint": helper["AUTH"] + "/api/accounts/authorize",
                    "token_endpoint": helper["TOKEN"],
                }
            if url == helper["TOKEN"]:
                self.assertTrue(form)
                expected = (
                    base64.urlsafe_b64encode(
                        hashlib.sha256(body["code_verifier"].encode()).digest()
                    )
                    .decode()
                    .rstrip("=")
                )
                self.assertEqual(expected, parameters["code_challenge"][0])
                self.assertEqual(body["redirect_uri"], parameters["redirect_uri"][0])
                self.assertEqual(body["client_id"], "oaiapp_standalone_test")
                self.assertNotIn("client_secret", body)
                return {
                    "access_token": "synthetic-access",
                    "refresh_token": "synthetic-refresh",
                    "id_token": "synthetic-id",
                    "token_type": "Bearer",
                    "scope": "synthetic-scopes",
                    "expires_in": 3600,
                }
            self.assertEqual(url, origin + helper["PREFIX"] + "/pairing/complete")
            self.assertEqual(body["tokens"]["access_token"], "synthetic-access")
            return {"state": "connected"}

        def browser(url):
            parsed = urlsplit(url)
            self.assertEqual(parsed.netloc, "auth.openai.com")
            parameters.update(parse_qs(parsed.query))
            self.assertEqual(parameters["agent_name_hint"], ["mealf"])
            callback = urlsplit(parameters["redirect_uri"][0])
            self.assertEqual(callback.hostname, "127.0.0.1")

            def callback_request():
                try:
                    connection = http.client.HTTPConnection("127.0.0.1", callback.port, timeout=5)
                    connection.request(
                        "GET",
                        callback.path
                        + "?"
                        + urlencode(
                            {
                                "state": parameters["state"][0],
                                "code": "synthetic-code",
                                "client_id": "oaiapp_standalone_test",
                            }
                        ),
                    )
                    response = connection.getresponse()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.getheader("Cache-Control"), "no-store")
                    response.read()
                    connection.close()
                except Exception as exc:
                    thread_errors.append(type(exc).__name__)

            thread = threading.Thread(target=callback_request, daemon=True)
            thread.start()
            threads.append(thread)
            return True

        with (
            tempfile.TemporaryDirectory(prefix="mealf-connector-test-") as temporary,
            patch.dict(os.environ, {"APPDATA": temporary}),
        ):
            self.assertEqual(helper["local_host_id"](), helper["local_host_id"]())
            result = helper["connect"](
                origin,
                "synthetic_pairing_capability_123456789",
                request=request,
                open_browser=browser,
            )
            self.assertEqual(result["state"], "connected")
            for thread in threads:
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
            self.assertEqual(thread_errors, [])
            self.assertEqual(len(calls), 4)
            for path in Path(temporary).rglob("*"):
                if path.is_file():
                    data = json.loads(path.read_text())
                    self.assertEqual(set(data), {"host_id"})

    def test_server_url_requires_https_origin(self):
        for invalid in [
            "http://mealf.example",
            "https://user:password@mealf.example",
            "https://mealf.example/?secret=value",
            "https://mealf.example/path",
            "https://mealf.example/#x",
        ]:
            with self.subTest(url=invalid), self.assertRaises(helper["ConnectError"]):
                helper["server_origin"](invalid)


if __name__ == "__main__":
    unittest.main()
