#!/usr/bin/env python3
"""mealf ChatGPT connector. Standalone Python 3.10+, standard library only.

Run on the Windows/Linux/macOS computer running your browser, not in the NAS terminal.
No household password, API key, browser cookie or persisted OAuth token is required.
"""

import argparse
import base64
import getpass
import hashlib
import json
import os
import re
import secrets
import socket
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from uuid import UUID, uuid4

AUTH = "https://auth.openai.com"
TOKEN = AUTH + "/api/accounts/oauth/token"
RESOURCE = "https://api.openai.com/v1"
SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
PREFIX = "/api/v1/integrations/chatgpt"
LIMIT = 500_000


class ConnectError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ConnectError("redirect_refused")


def request_json(url, body=None, *, form=False):
    headers = {"Accept": "application/json", "Accept-Encoding": "identity"}
    data = None
    if body is not None:
        headers["Content-Type"] = (
            "application/x-www-form-urlencoded" if form else "application/json"
        )
        data = (urllib.parse.urlencode(body) if form else json.dumps(body)).encode()
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        # Preserve OS TLS verification, normal proxies and certificate configuration.
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
            if response.headers.get("Content-Encoding", "identity") != "identity":
                raise ConnectError("response_invalid")
            raw = response.read(LIMIT + 1)
            if len(raw) > LIMIT:
                raise ConnectError("response_too_large")
            value = json.loads(raw) if raw else {}
            if not isinstance(value, dict):
                raise ConnectError("response_invalid")
            return value
    except (urllib.error.URLError, OSError, ValueError, RecursionError) as exc:
        # URLs, exception bodies and HTTP headers can contain credentials.
        raise ConnectError("connection_failed") from exc


def server_origin(value):
    parsed = urllib.parse.urlsplit(value.strip())
    try:
        parsed.port
    except ValueError as exc:
        raise ConnectError("server_url_invalid") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or any(ord(c) <= 32 for c in value)
    ):
        raise ConnectError("server_url_invalid")
    return urllib.parse.urlunsplit(("https", parsed.netloc, "", "", ""))


def local_host_id():
    root = Path(os.environ.get("APPDATA") or Path.home() / ".config") / "mealf"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / "chatgpt-helper-host.json"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor) as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ConnectError("host_identity_invalid")
            value = json.loads(handle.read(1000))["host_id"]
            if not isinstance(value, str) or not value.startswith("urn:uuid:"):
                raise ConnectError("host_identity_invalid")
            UUID(value[9:])
            return value
    with os.fdopen(descriptor, "w") as handle:
        value = "urn:uuid:" + str(uuid4())
        json.dump({"host_id": value}, handle)
        handle.flush()
        os.fsync(handle.fileno())
    return value


def connect(
    server, code, *, request=request_json, open_browser=webbrowser.open, host=local_host_id
):
    server = server_origin(server)
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", code):
        raise ConnectError("pairing_code_invalid")
    nonce_state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    result: dict[str, str] = {}

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            valid = False
            try:
                parsed = urllib.parse.urlsplit(self.path)
                query = urllib.parse.parse_qs(
                    parsed.query, keep_blank_values=True, max_num_fields=12
                )
                valid = (
                    len(self.path) <= 4096
                    and parsed.path == "/auth/callback"
                    and self.headers.get("Host") == f"127.0.0.1:{listener.server_port}"
                    and all(len(v) == 1 for v in query.values())
                    and secrets.compare_digest(query.get("state", [""])[0], nonce_state)
                    and not result
                )
                if valid:
                    if "error" in query:
                        result["error"] = "authorization_declined"
                    elif not query.get("code", [""])[0]:
                        result["error"] = "callback_invalid"
                    else:
                        result.update({k: v[0] for k, v in query.items()})
            except (ValueError, TypeError):
                pass
            self.send_response(200 if valid else 400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
            )
            self.end_headers()
            self.wfile.write(
                b"Return to the mealf connector terminal."
                if valid
                else b"Invalid sign-in callback."
            )

    class Listener(HTTPServer):
        def get_request(self):
            sock, address = super().get_request()
            sock.settimeout(3)
            return sock, address

        def handle_error(self, request, client_address):
            pass

    with Listener(("127.0.0.1", 0), Callback) as listener:
        listener.timeout = 0.5
        redirect = f"http://127.0.0.1:{listener.server_port}/auth/callback"
        bootstrap = request(server + PREFIX + "/pairing/claim", {"code": code})
        metadata = request(AUTH + "/.well-known/openid-configuration")
        if (
            metadata.get("issuer") != AUTH
            or metadata.get("authorization_endpoint") != AUTH + "/api/accounts/authorize"
            or metadata.get("token_endpoint") != TOKEN
        ):
            raise ConnectError("provider_configuration_changed")
        client_id = bootstrap.get("client_id")
        if client_id != "dynamic_agent_client" and not re.fullmatch(
            r"oaiapp_[A-Za-z0-9_-]{3,200}", str(client_id)
        ):
            raise ConnectError("client_invalid")
        params = {
            "client_id": client_id,
            "ext_agent_host_id": host(),
            "response_type": "code",
            "redirect_uri": redirect,
            "scope": SCOPES,
            "resource": RESOURCE,
            "state": nonce_state,
            "nonce": bootstrap["nonce"],
            "code_challenge_method": "S256",
            "code_challenge": challenge,
        }
        if client_id == "dynamic_agent_client":
            params["agent_name_hint"] = "mealf"
        elif bootstrap.get("id_token_hint"):
            params["id_token_hint"] = bootstrap["id_token_hint"]
        # Never print this URL: a returning sign-in may contain a protected ID hint.
        if not open_browser(
            metadata["authorization_endpoint"] + "?" + urllib.parse.urlencode(params)
        ):
            raise ConnectError("browser_unavailable")
        deadline = time.monotonic() + 600
        while not result and time.monotonic() < deadline:
            listener.handle_request()
        if not result:
            raise ConnectError("sign_in_timed_out")
        if "error" in result:
            raise ConnectError("authorization_declined")
    issued = result.get("client_id", client_id)
    if not re.fullmatch(r"oaiapp_[A-Za-z0-9_-]{3,200}", str(issued)) or (
        client_id != "dynamic_agent_client" and issued != client_id
    ):
        raise ConnectError("client_invalid")
    tokens = request(
        TOKEN,
        {
            "grant_type": "authorization_code",
            "client_id": issued,
            "code": result["code"],
            "code_verifier": verifier,
            "redirect_uri": redirect,
            "resource": RESOURCE,
        },
        form=True,
    )
    fields = {
        "access_token",
        "refresh_token",
        "id_token",
        "token_type",
        "expires_in",
        "scope",
        "earliest_refresh_at",
    }
    approved = request(
        server + PREFIX + "/pairing/complete",
        {
            "code": code,
            "client_id": issued,
            "tokens": {k: v for k, v in tokens.items() if k in fields},
        },
    )
    if approved.get("state") != "connected":
        raise ConnectError("connection_not_enabled")
    return approved


def main():
    parser = argparse.ArgumentParser(
        description="Connect your personal ChatGPT plan to your own mealf server."
    )
    parser.add_argument("--server", help="HTTPS origin of your mealf installation")
    parser.add_argument("--language", choices=["en", "de"], default="en")
    args = parser.parse_args()
    german = args.language == "de"
    try:
        if not sys.stdin.isatty():
            raise ConnectError("interactive_terminal_required")
        server = args.server or input("mealf HTTPS URL: ")
        print(
            "Kopple nur deinen eigenen Server und deine eigene Sitzung."
            if german
            else "Connect only your own server and personal mealf session."
        )
        code = getpass.getpass(
            "Kopplungscode (Eingabe verborgen): " if german else "Pairing code (hidden): "
        ).strip()
        print(
            "Die OpenAI-Anmeldung wird im Browser geöffnet."
            if german
            else "Opening OpenAI sign-in in your browser."
        )
        connect(server, code)
        print(
            "Verbunden. Wähle in mealf ein Modell und importiere einen Rezepttext."
            if german
            else "Connected. Return to mealf, choose a model and import recipe text."
        )
    except (
        ConnectError,
        OSError,
        ValueError,
        KeyError,
        KeyboardInterrupt,
        EOFError,
        socket.timeout,
    ):
        print(
            "Verbindung nicht bestätigt. Prüfe mealf und erstelle bei Bedarf einen neuen Code. Entferne eine unvollständige Verbindung in den ChatGPT-Einstellungen."
            if german
            else "Connection not confirmed. Check mealf and prepare a new code if needed. Disconnect an unfinished connection in ChatGPT Settings."
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
