"""Supported OpenAI OSS OAuth and Responses transport; never consumer backend endpoints."""

import json
import secrets
import time

import httpx
import jwt
from pydantic import ValidationError

from .ai import EXTRACTION_SYSTEM
from .errors import DomainError
from .recipe_extraction import ExtractionResult

ISSUER = "https://auth.openai.com"
DISCOVERY = ISSUER + "/.well-known/openid-configuration"
AUTHORIZE = ISSUER + "/api/accounts/authorize"
TOKEN = ISSUER + "/api/accounts/oauth/token"
JWKS = ISSUER + "/.well-known/jwks.json"
RESOURCE = "https://api.openai.com/v1"
SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
REQUIRED_SCOPES = {"resource.invoke", "chatgpt.tokens.use.direct", "offline_access"}
MAX_RESPONSE = 500_000


def provider_error(value, status=502):
    code = value.get("code") if isinstance(value, dict) else None
    if code == "subscription_sharing_user_not_eligible":
        return DomainError("chatgpt_not_eligible", 409)
    if code == "subscription_sharing_usage_limit_exceeded":
        return DomainError("chatgpt_usage_limit", 429)
    if code == "subscription_sharing_usage_unavailable":
        return DomainError("chatgpt_usage_unavailable", 503)
    if status in (401, 403):
        return DomainError("chatgpt_reconnect_required", 409)
    if status == 429:
        return DomainError("chatgpt_usage_limit", 429)
    return DomainError("chatgpt_provider_unavailable", 502)


class ChatGPTProtocol:
    def __init__(self, transport=None):
        self.transport = transport
        self._keys = None
        self._keys_at = 0.0
        self._metadata = None

    def client(self):
        return httpx.Client(timeout=30, follow_redirects=False, transport=self.transport)

    def json(self, method, url, *, form=None, access=None):
        headers = {"Accept": "application/json", "Accept-Encoding": "identity"}
        if access:
            headers["Authorization"] = "Bearer " + access
        try:
            with (
                self.client() as client,
                client.stream(method, url, data=form, headers=headers) as response,
            ):
                data = bytearray()
                for part in response.iter_bytes():
                    data.extend(part)
                    if len(data) > MAX_RESPONSE:
                        raise DomainError("chatgpt_response_too_large", 502)
                try:
                    body = json.loads(data)
                except (ValueError, RecursionError):
                    body = {}
                if response.status_code != 200:
                    if url == TOKEN and isinstance(body, dict):
                        if body.get("error") == "invalid_grant":
                            raise DomainError("chatgpt_reconnect_required", 409)
                    raise provider_error(
                        body.get("error") if isinstance(body, dict) else None,
                        response.status_code,
                    )
                if not isinstance(body, dict):
                    raise DomainError("chatgpt_invalid_response", 502)
                return body
        except httpx.HTTPError as exc:
            raise DomainError("chatgpt_connection_unavailable", 503) from exc

    def discovery(self):
        if self._metadata is None:
            value = self.json("GET", DISCOVERY)
            for key, expected in {
                "issuer": ISSUER,
                "authorization_endpoint": AUTHORIZE,
                "token_endpoint": TOKEN,
                "jwks_uri": JWKS,
            }.items():
                if value.get(key) != expected:
                    raise DomainError("chatgpt_discovery_changed", 502)
            self._metadata = value
        return self._metadata

    def claims(self, token, audience, *, nonce=None):
        self.discovery()
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if (
                header.get("alg") not in ("RS256", "ES256")
                or not isinstance(kid, str)
                or len(kid) > 200
                or header.get("crit")
            ):
                raise ValueError("Unsupported signature")
            for retry in range(2):
                if self._keys is None or time.monotonic() - self._keys_at > 3600 or retry:
                    self._keys = self.json("GET", JWKS).get("keys")
                    self._keys_at = time.monotonic()
                if not isinstance(self._keys, list) or len(self._keys) > 100:
                    raise ValueError("Invalid key set")
                matches = [k for k in self._keys if isinstance(k, dict) and k.get("kid") == kid]
                if matches:
                    break
            if len(matches) != 1:
                raise ValueError("Unknown signature")
            key = jwt.PyJWK.from_dict(matches[0])
            if key.algorithm_name != header["alg"]:
                raise ValueError("Signature mismatch")
            claims = jwt.decode(
                token,
                key.key,
                algorithms=[header["alg"]],
                audience=audience,
                issuer=ISSUER,
                options={"require": ["exp", "iat", "iss", "sub", "aud"]},
                leeway=15,
            )
            if (
                not isinstance(claims["sub"], str)
                or not 1 <= len(claims["sub"]) <= 200
                or (isinstance(claims["aud"], list) and claims.get("azp") != audience)
                or (
                    nonce is not None
                    and not secrets.compare_digest(str(claims.get("nonce", "")), nonce)
                )
            ):
                raise ValueError("Identity mismatch")
            return claims
        except (jwt.PyJWTError, ValueError, TypeError, KeyError) as exc:
            raise DomainError("chatgpt_identity_invalid", 422) from exc

    def credentials(self, raw, client_id, *, nonce=None, previous=None, subject=None):
        try:
            if str(raw.get("token_type", "")).lower() != "bearer":
                raise ValueError("Unsupported token")
            for name in ("access_token", "refresh_token"):
                if not isinstance(raw.get(name), str) or not 1 <= len(raw[name]) <= 16384:
                    raise ValueError("Missing credential")
            saved_id = raw.get("id_token") or (previous or {}).get("id_token")
            if not isinstance(saved_id, str) or len(saved_id) > 16384:
                raise ValueError("Missing identity")
            # A retained ID token is a login hint, not a renewed identity assertion.
            identity = None
            if nonce is not None or saved_id != (previous or {}).get("id_token"):
                identity = self.claims(saved_id, client_id, nonce=nonce)
                if subject is not None and identity["sub"] != subject:
                    raise ValueError("Account changed")
                subject = identity["sub"]
            access = self.claims(raw["access_token"], RESOURCE)
            if access["sub"] != subject or access.get("client_id") != client_id:
                raise ValueError("Credentials belong to another registration")
            scopes = raw.get("scope", (previous or {}).get("scope", ""))
            if not isinstance(scopes, str) or not isinstance(access.get("scope"), str):
                raise ValueError("Missing permission")
            if not REQUIRED_SCOPES <= set(scopes.split()) & set(access["scope"].split()):
                raise DomainError("chatgpt_plan_permission_required", 409)
            lifetime = raw.get("expires_in")
            if (
                isinstance(lifetime, bool)
                or not isinstance(lifetime, int)
                or not 0 < lifetime <= 86400
            ):
                raise ValueError("Invalid expiry")
            earliest = raw.get("earliest_refresh_at", 0)
            if not isinstance(earliest, (int, float)) or not 0 <= earliest < 1e12:
                raise ValueError("Invalid renewal time")
            return {
                "access_token": raw["access_token"],
                "refresh_token": raw["refresh_token"],
                "id_token": saved_id,
                "scope": scopes,
            }, {
                "subject": subject,
                "label": str(
                    (identity or {}).get("email")
                    or (previous or {}).get("label")
                    or "ChatGPT account"
                )[:254],
                "expires_at": min(time.time() + lifetime, float(access["exp"])),
                "earliest_refresh_at": earliest,
            }
        except (ValueError, TypeError, KeyError) as exc:
            raise DomainError("chatgpt_credentials_invalid", 422) from exc

    def models(self, access):
        from .chatgpt_models import ChatGPTModel, ChatGPTModelCatalog

        body = self.json("GET", RESOURCE + "/models", access=access)
        raw = body.get("models")
        if not isinstance(raw, list) or len(raw) > 1000:
            raise DomainError("chatgpt_invalid_response", 502)
        try:
            models = [
                ChatGPTModel(slug=m["slug"], display_name=m["display_name"])
                for m in raw
                if isinstance(m, dict) and m.get("visibility") == "list"
            ]
            if len({m.slug for m in models}) != len(models):
                raise ValueError("Duplicate model")
            return ChatGPTModelCatalog(models=models)
        except (ValueError, KeyError) as exc:
            raise DomainError("chatgpt_invalid_response", 502) from exc

    def extract(self, access, model, text):
        if not isinstance(text, str) or not text.strip() or len(text.encode()) > 50000:
            raise DomainError("chatgpt_text_required", 422)
        body = {
            "model": model,
            "instructions": EXTRACTION_SYSTEM
            + "\nJSON schema:\n"
            + json.dumps(ExtractionResult.model_json_schema()),
            "input": [{"role": "user", "content": [{"type": "input_text", "text": text}]}],
            "store": False,
            "stream": True,
        }
        try:
            with (
                self.client() as client,
                client.stream(
                    "POST",
                    RESOURCE + "/responses",
                    json=body,
                    headers={
                        "Authorization": "Bearer " + access,
                        "Accept": "text/event-stream",
                        "Accept-Encoding": "identity",
                    },
                ) as response,
            ):
                if response.status_code != 200:
                    data = bytearray()
                    for part in response.iter_bytes():
                        data.extend(part)
                        if len(data) > MAX_RESPONSE:
                            raise DomainError("chatgpt_response_too_large", 502)
                    # Error bodies are untrusted and never surfaced verbatim.
                    try:
                        error = json.loads(data[:MAX_RESPONSE]).get("error")
                    except (ValueError, AttributeError):
                        error = None
                    raise provider_error(error, response.status_code)
                size = 0
                buffer = b""
                event = []
                completed = None
                deadline = time.monotonic() + 90
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_RESPONSE or time.monotonic() > deadline:
                        raise DomainError("chatgpt_response_too_large", 502)
                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        line = line.rstrip(b"\r")
                        if line.startswith(b"data:"):
                            event.append(line[5:].lstrip(b" "))
                        elif not line and event:
                            raw = b"\n".join(event)
                            event = []
                            if raw == b"[DONE]":
                                continue
                            value = json.loads(raw)
                            if not isinstance(value, dict):
                                raise ValueError("Invalid event")
                            kind = value.get("type")
                            if kind in ("error", "response.failed"):
                                failed = value.get("response", value)
                                raise provider_error(failed.get("error", failed))
                            if kind == "response.incomplete":
                                raise DomainError("chatgpt_output_incomplete", 502)
                            if kind == "response.completed":
                                if completed is not None:
                                    raise ValueError("Repeated completion")
                                completed = value.get("response")
                if (
                    buffer.strip()
                    or event
                    or not isinstance(completed, dict)
                    or completed.get("status") != "completed"
                ):
                    raise DomainError("chatgpt_output_incomplete", 502)
                output = completed.get("output")
                if not isinstance(output, list):
                    raise ValueError("Missing output")
                parts = []
                for item in output:
                    if item.get("type") != "message":
                        continue
                    for content in item.get("content", []):
                        if content.get("type") == "refusal":
                            raise DomainError("chatgpt_extraction_refused", 422)
                        if content.get("type") == "output_text":
                            parts.append(content["text"])
                return ExtractionResult.model_validate(json.loads("".join(parts)))
        except httpx.HTTPError as exc:
            raise DomainError("chatgpt_connection_unavailable", 503) from exc
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            ValidationError,
            RecursionError,
        ) as exc:
            raise DomainError("chatgpt_invalid_recipe_response", 502) from exc
