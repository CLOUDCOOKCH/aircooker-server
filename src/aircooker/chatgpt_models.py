"""Public connection shapes contain no OAuth credentials or other sessions' identity."""

from typing import Literal
from uuid import UUID

from pydantic import Field, SecretStr

from .models import Model


class ChatGPTStatus(Model):
    state: Literal["disconnected", "connected", "reconnect_required"]
    connection_id: UUID | None = None
    account_label: str | None = None
    model: str | None = None
    error_code: str | None = None
    input_formats: list[Literal["text"]] = ["text"]


class ChatGPTPairRequest(Model):
    personal_use_confirmed: Literal[True]


class ChatGPTPairing(Model):
    id: UUID
    code: str
    expires_at: float


class ChatGPTPairCode(Model):
    code: SecretStr = Field(min_length=32, max_length=128)


class ChatGPTClaim(ChatGPTPairCode):
    pass


class ChatGPTBootstrap(Model):
    nonce: str
    client_id: str
    id_token_hint: str | None = Field(default=None, repr=False)
    host_id: str


class ChatGPTTokenSet(Model):
    access_token: SecretStr = Field(min_length=1, max_length=16384)
    refresh_token: SecretStr = Field(min_length=1, max_length=16384)
    id_token: SecretStr = Field(min_length=1, max_length=16384)
    token_type: str = Field(max_length=20)
    expires_in: int = Field(gt=0, le=86400)
    scope: str = Field(max_length=2048)
    earliest_refresh_at: float = Field(default=0, ge=0, allow_inf_nan=False)


class ChatGPTComplete(ChatGPTPairCode):
    client_id: str = Field(pattern=r"^oaiapp_[A-Za-z0-9_-]{3,200}$")
    tokens: ChatGPTTokenSet


class ChatGPTModel(Model):
    slug: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)


class ChatGPTModelCatalog(Model):
    models: list[ChatGPTModel] = Field(max_length=100)


class ChatGPTSelection(Model):
    connection_id: UUID
    model: str = Field(min_length=1, max_length=200)


class ChatGPTDisconnect(Model):
    remote_revocation_confirmed: bool
