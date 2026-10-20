"""Administrator-controlled encrypted AI configuration; never expose stored credentials."""

import json
from dataclasses import asdict
from typing import Literal

from pydantic import Field

from .ai import AIConfiguration
from .errors import DomainError
from .models import Model
from .secrets import SecretVault


class AISettings(Model):
    enabled: bool = True
    provider: Literal["openai", "openai-compatible", "anthropic", "ollama", "openwebui"] = "openai"
    base_url: str = Field(default="https://api.openai.com/v1", min_length=1, max_length=2048)
    model: str = Field(default="", max_length=200)
    api_key: str | None = Field(
        default=None, max_length=8192, repr=False, json_schema_extra={"writeOnly": True}
    )
    timeout: int = Field(default=30, ge=1, le=120)
    max_content: int = Field(default=50000, ge=100, le=100000)
    requests_per_hour: int = Field(default=20, ge=1, le=1000)
    structured_output: bool = False
    allow_local_http: bool = False


class AISettingsStatus(Model):
    enabled: bool
    origin: Literal["saved", "environment", "disabled"]
    provider: str | None = None
    base_url: str | None = None
    model: str | None = None
    key_configured: bool = False
    timeout: int = 30
    max_content: int = 50000
    requests_per_hour: int = 20
    structured_output: bool = False
    allow_local_http: bool = False
    text_extraction: bool = True
    image_extraction: bool = False
    live_verified: bool = False
    configuration_error: str | None = None


def load_configuration(root):
    try:
        raw = SecretVault(root).load("ai-provider")
        if raw is not None:
            values = json.loads(raw)
            return AIConfiguration(**values["configuration"]) if values.get("enabled") else None
        return AIConfiguration.from_environment()
    except (OSError, TypeError, ValueError, KeyError) as exc:
        raise DomainError("ai_configuration_unavailable", 503) from exc


def settings_status(root):
    configured = (root / "ai-provider.enc").exists()
    try:
        config = load_configuration(root)
    except DomainError as exc:
        return AISettingsStatus(
            enabled=False,
            origin="saved" if configured else "environment",
            configuration_error=exc.code,
        )
    if config is None:
        return AISettingsStatus(enabled=False, origin="saved" if configured else "disabled")
    values = asdict(config)
    key = values.pop("api_key")
    return AISettingsStatus(
        enabled=True,
        origin="saved" if configured else "environment",
        key_configured=bool(key),
        **values,
    )


def save_configuration(root, body: AISettings):
    vault = SecretVault(root)
    if not body.enabled:
        vault.save("ai-provider", json.dumps({"enabled": False}))
        return settings_status(root)
    try:
        previous = load_configuration(root)
    except DomainError:
        previous = None
    # A retained key is bound to its provider and endpoint. Editing the destination
    # never silently sends an existing credential to a different service.
    key = body.api_key
    if key is None:
        same = (
            previous
            and previous.provider == body.provider
            and previous.base_url.rstrip("/") == body.base_url.rstrip("/")
        )
        key = previous.api_key if same else ""
    config = AIConfiguration(**body.model_dump(exclude={"enabled", "api_key"}), api_key=key)
    vault.save("ai-provider", json.dumps({"enabled": True, "configuration": asdict(config)}))
    return settings_status(root)
