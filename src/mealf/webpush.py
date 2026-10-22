"""Replaceable standards-based push transport; no imported URL can select a destination."""

import base64
import hashlib
import http.client
import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from py_vapid import Vapid
from pywebpush import WebPusher

from .errors import DomainError
from .importing import PinnedHTTPS, public_addresses
from .secrets import SecretVault


@dataclass(frozen=True)
class PushResponse:
    status: int
    retry_after: int | None = None


def retry_delay(value: str | None):
    if not value or len(value) > 100:
        return None
    try:
        if value.isdecimal():
            seconds = int(value)
        else:
            instant = parsedate_to_datetime(value)
            if instant.tzinfo is None:
                return None
            seconds = int((instant - datetime.now(UTC)).total_seconds())
        return max(0, min(3600, seconds))
    except (ValueError, TypeError, OverflowError):
        return None


def encoded(value: bytes):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def key_bytes(value: str, size: int):
    if not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", value):
        raise ValueError("Invalid push key")
    raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    if len(raw) != size:
        raise ValueError("Invalid push key size")
    return raw


def endpoint_origin(endpoint: str):
    try:
        url = urlsplit(endpoint)
        host = url.hostname or ""
        allowed = (
            host.endswith(".push.apple.com")
            or host == "fcm.googleapis.com"
            or host == "updates.push.services.mozilla.com"
        )
        if (
            not allowed
            or url.scheme != "https"
            or url.port not in (None, 443)
            or url.username is not None
            or url.password is not None
            or url.fragment
            or not url.path.startswith("/")
            or any(ord(c) <= 32 or ord(c) >= 127 for c in endpoint)
            or "\\" in endpoint
        ):
            raise ValueError("Unsupported push endpoint")
        return "https://" + host
    except ValueError as exc:
        raise DomainError("push_endpoint_unsupported", 422) from exc


class WebPushTransport:
    def __init__(self, vault: SecretVault, subject: str):
        self.vault = vault
        self.subject = subject
        raw = vault.load("webpush-vapid")
        if raw is None:
            key = ec.generate_private_key(ec.SECP256R1())
            raw = key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ).decode()
            vault.save("webpush-vapid", raw)
        self.vapid = Vapid.from_pem(raw.encode())
        self.public_key = encoded(
            self.vapid.public_key.public_bytes(
                serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
            )
        )

    def send(self, subscription: dict, message: dict, tag: str, ttl: int):
        endpoint = subscription["endpoint"]
        origin = endpoint_origin(endpoint)
        url = urlsplit(endpoint)
        # Pin the actual socket to a public resolved address. TLS verifies the vendor host.
        addresses = public_addresses(url.hostname, 443)
        body = WebPusher(subscription).encode(json.dumps(message).encode())["body"]
        headers = {
            **self.vapid.sign(
                {"aud": origin, "sub": self.subject, "exp": int(time.time()) + 12 * 3600}
            ),
            "Content-Encoding": "aes128gcm",
            "Content-Type": "application/octet-stream",
            "TTL": str(max(0, min(900, ttl))),
            "Topic": encoded(hashlib.sha256(tag.encode()).digest())[:32],
            "Urgency": "normal",
        }
        connection = PinnedHTTPS(url.hostname, addresses[0])
        try:
            connection.request(
                "POST", url.path + ("?" + url.query if url.query else ""), body, headers
            )
            response = connection.getresponse()
            # No connection pooling: discard the vendor body without downloading it.
            try:
                delay = retry_delay(response.getheader("Retry-After"))
                return PushResponse(response.status, delay)
            finally:
                response.close()
        except (OSError, http.client.HTTPException) as exc:
            raise DomainError("push_network_failed", 503) from exc
        finally:
            connection.close()
