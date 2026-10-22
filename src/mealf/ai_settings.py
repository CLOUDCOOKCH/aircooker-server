"""Administrator-controlled encrypted AI configuration; never expose stored credentials."""

import json
from dataclasses import asdict
from typing import Literal

from pydantic import Field, model_validator

from .ai import PROVIDER_ENDPOINTS, PROVIDER_FORMATS, AIConfiguration
from .errors import DomainError
from .models import Model
from .secrets import SecretVault


class AISettings(Model):
    enabled: bool = True
    provider: Literal[
        "gemini", "openai", "openrouter", "openai-compatible", "anthropic", "ollama", "openwebui"
    ] = "gemini"
    base_url: str = Field(default="", max_length=2048)
    model: str = Field(default="", max_length=200)
    api_key: str | None = Field(
        default=None, max_length=8192, repr=False, json_schema_extra={"writeOnly": True}
    )
    timeout: int = Field(default=30, ge=1, le=120)
    max_content: int = Field(default=50000, ge=100, le=100000)
    requests_per_hour: int = Field(default=20, ge=1, le=1000)
    structured_output: bool = False
    allow_local_http: bool = False
    input_formats: list[Literal["text", "image", "pdf", "video", "youtube"]] = Field(
        default=["text"], max_length=5
    )

    @model_validator(mode="after")
    def default_endpoint(self):
        if not self.base_url:
            self.base_url = PROVIDER_ENDPOINTS[self.provider]
        return self


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
    pdf_extraction: bool = False
    video_extraction: bool = False
    input_formats: list[str] = Field(default_factory=lambda: ["text"])
    available_formats: list[str] = Field(default_factory=list)
    live_verified: bool = False
    configuration_error: str | None = None


class AIProviderCatalog(Model):
    enabled: bool
    default_provider: str
    profiles: list[AISettingsStatus]


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
    values["input_formats"] = list(config.formats)
    return AISettingsStatus(
        enabled=True,
        origin="saved" if configured else "environment",
        key_configured=bool(key),
        available_formats=list(PROVIDER_FORMATS[config.provider]),
        image_extraction="image" in config.formats,
        pdf_extraction="pdf" in config.formats,
        video_extraction=bool({"video", "youtube"} & set(config.formats)),
        **values,
    )


def provider_catalog(root):
    selected = settings_status(root)
    profiles = []
    saved = _saved_values(root)
    for provider, endpoint in PROVIDER_ENDPOINTS.items():
        value = saved.get("profiles", {}).get(provider)
        if value:
            config = AIConfiguration(**value)
            profiles.append(_profile_status(config))
        elif selected.provider == provider:
            profiles.append(selected)
        else:
            profiles.append(
                AISettingsStatus(
                    enabled=False,
                    origin="disabled",
                    provider=provider,
                    base_url=endpoint,
                    available_formats=list(PROVIDER_FORMATS[provider]),
                )
            )
    return AIProviderCatalog(
        enabled=selected.enabled,
        default_provider=selected.provider
        or saved.get("configuration", {}).get("provider", "gemini"),
        profiles=profiles,
    )


def _saved_values(root):
    try:
        raw = SecretVault(root).load("ai-provider")
        saved = json.loads(raw) if raw is not None else {}
        if not isinstance(saved, dict) or not isinstance(saved.get("profiles", {}), dict):
            raise ValueError("Invalid saved profile collection")
        profiles = saved.setdefault("profiles", {})
        if saved.get("configuration"):
            profiles.setdefault(saved["configuration"]["provider"], saved["configuration"])
        return saved
    except (DomainError, OSError, ValueError, TypeError, KeyError):
        return {"profiles": {}}


def _profile_status(config):
    values = asdict(config)
    key = values.pop("api_key")
    values["input_formats"] = list(config.formats)
    return AISettingsStatus(
        enabled=True,
        origin="saved",
        key_configured=bool(key),
        available_formats=list(PROVIDER_FORMATS[config.provider]),
        image_extraction="image" in config.formats,
        pdf_extraction="pdf" in config.formats,
        video_extraction=bool({"video", "youtube"} & set(config.formats)),
        **values,
    )


def save_configuration(root, body: AISettings):
    vault = SecretVault(root)
    saved = _saved_values(root)
    if not body.enabled:
        saved["enabled"] = False
        vault.save("ai-provider", json.dumps(saved))
        return settings_status(root)
    try:
        retained = saved.get("profiles", {}).get(body.provider)
        previous = AIConfiguration(**retained) if retained else load_configuration(root)
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
        key = previous.api_key if same and previous is not None else ""
    config = AIConfiguration(**body.model_dump(exclude={"enabled", "api_key"}), api_key=key)
    saved.setdefault("profiles", {})[body.provider] = asdict(config)
    saved.update(enabled=True, configuration=asdict(config))
    vault.save("ai-provider", json.dumps(saved))
    return settings_status(root)
