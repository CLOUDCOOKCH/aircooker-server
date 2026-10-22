from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .recipe_extraction import ExtractionResult, RecipeTimes, RecipeYield, StepDetails

Positive = Annotated[Decimal, Field(gt=0, le=1000000)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Ingredient(Model):
    id: UUID
    name: str = Field(min_length=1, max_length=200)
    quantity: Annotated[Decimal, Field(ge=0, le=1000000)] | None = None
    quantity_max: Annotated[Decimal, Field(ge=0, le=1000000)] | None = None
    unit: str = Field(default="", max_length=30)
    preparation: str = Field(default="", max_length=300)
    original_text: str = Field(default="", max_length=500)
    quantity_text: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=5000)
    optional: bool = False
    group: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def valid_range(self):
        if self.quantity_max is not None and (
            self.quantity is None or self.quantity_max < self.quantity
        ):
            raise ValueError("Invalid quantity range")
        return self


class Recipe(Model):
    schema_version: Literal["1.0.0"] = "1.0.0"
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    source_url: str | None = Field(default=None, max_length=2048)
    source_platform: str = Field(default="manual", max_length=50)
    image_id: UUID | None = None
    servings: Positive = Decimal(2)
    ingredients: list[Ingredient] = Field(default_factory=list, max_length=300)
    steps: list[Annotated[str, Field(min_length=1, max_length=5000)]] = Field(
        default_factory=list, max_length=200
    )
    notes: str = Field(default="", max_length=10000)
    rating: int | None = Field(default=None, ge=1, le=5)
    nutrition: dict[str, str] | None = None
    nutrition_source: str | None = Field(default=None, max_length=2048)
    provenance: dict[str, str] = Field(default_factory=dict, max_length=50)
    times: RecipeTimes = Field(default_factory=RecipeTimes)
    language: str | None = Field(default=None, max_length=50)
    yield_info: RecipeYield | None = None
    category: str | None = Field(default=None, max_length=5000)
    cuisine: str | None = Field(default=None, max_length=5000)
    tags: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        default_factory=list, max_length=50
    )
    instruction_details: list[StepDetails] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def unique_ingredient_ids(self):
        if len({item.id for item in self.ingredients}) != len(self.ingredients):
            raise ValueError("Ingredient identifiers must be unique within a recipe")
        return self


class Recurrence(Model):
    interval_weeks: int = Field(default=1, ge=1, le=52)
    until: date
    exceptions: list[date] = Field(default_factory=list, max_length=520)


class Meal(Model):
    recipe_id: UUID
    date: date
    category: Literal["breakfast", "lunch", "dinner"]
    servings: Positive = Decimal(2)
    order: int = Field(default=0, ge=0, le=100)
    leftover_id: UUID | None = None
    recurrence: Recurrence | None = None
    cooked: bool = False

    @model_validator(mode="after")
    def valid_end(self):
        if self.leftover_id and self.recurrence:
            raise ValueError("Schedule leftover portions as individual meals")
        if self.recurrence and (
            self.recurrence.until < self.date or (self.recurrence.until - self.date).days > 3660
        ):
            raise ValueError("Recurrence must end within ten years")
        return self


class Pantry(Model):
    name: str = Field(min_length=1, max_length=200)
    available: bool = True
    include_this_week: bool = False
    include_week_start: date | None = None

    @field_validator("include_week_start")
    @classmethod
    def monday_period(cls, value):
        if value is not None and value.weekday() != 0:
            raise ValueError("Pantry period must start on Monday")
        return value


class Leftover(Model):
    recipe_id: UUID
    portions: Positive
    produced_on: date
    discarded: bool = False


class TemplateSlot(Model):
    weekday: int = Field(ge=0, le=6)
    category: Literal["breakfast", "lunch", "dinner"]
    recipe_id: UUID
    servings: Positive


class Template(Model):
    name: str = Field(min_length=1, max_length=200)
    meals: list[TemplateSlot] = Field(max_length=100)


EntityKind = Literal["recipe", "meal", "pantry", "leftover", "template"]
ENTITY_MODELS: dict[str, type[Model]] = {
    "recipe": Recipe,
    "meal": Meal,
    "pantry": Pantry,
    "leftover": Leftover,
    "template": Template,
}


class Mutation(Model):
    mutation_id: UUID
    entity_id: UUID
    kind: EntityKind
    operation: Literal["upsert", "delete"]
    base_revision: int = Field(ge=0)
    payload: Recipe | Meal | Pantry | Leftover | Template | None = None
    device_id: UUID
    client_timestamp: datetime
    idempotency_key: UUID


class SyncAnchor(Model):
    cursor: int = Field(ge=0)
    token: str = Field(pattern=r"^(root|[a-f0-9]{32})$")


class SyncState(SyncAnchor):
    instance_id: UUID
    requested_cursor: int
    requested_token: str | None


class Push(Model):
    checkpoint: SyncAnchor | None = None
    mutations: list[Mutation] = Field(min_length=1, max_length=100)


class Change(Model):
    revision: int
    kind: EntityKind
    entity_id: UUID
    deleted: bool
    payload: dict
    updated_at: str


class MutationResult(Model):
    mutation_id: UUID
    status: Literal["accepted", "deleted", "rejected_tombstone"]
    revision: int
    conflict: bool
    revision_token: str | None = None


class Pull(Model):
    changes: list[Change]
    cursor: int
    has_more: bool
    cursor_token: str


class SyncSnapshot(Model):
    instance_id: UUID
    checkpoint: SyncAnchor
    changes: list[Change]
    next_after: str | None


class Credentials(Model):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)
    device_id: UUID


class Setup(Credentials):
    password: str = Field(min_length=12, max_length=1024)
    name: str = Field(min_length=1, max_length=100)
    timezone: str = "UTC"
    language: Literal["en", "de"] = "en"

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value


class Tokens(Model):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = 900
    session_id: UUID


class Refresh(Model):
    refresh_token: str = Field(min_length=32, max_length=256)


class ImportRequest(Model):
    ai_account: Literal["household", "chatgpt"] = "household"
    chatgpt_connection_id: UUID | None = None
    consent_chatgpt_background: bool = False
    image_id: UUID | None = None
    request_id: UUID = Field(default_factory=uuid4)
    use_ai: bool = False
    consent_external_ai: bool = False
    source_url: str | None = Field(default=None, max_length=2048)
    text: str | None = Field(default=None, max_length=100000)
    source_id: UUID | None = None
    ai_destination: (
        tuple[
            Annotated[str, Field(min_length=1, max_length=2048)],
            Annotated[str, Field(min_length=1, max_length=2048)],
            Annotated[str, Field(min_length=1, max_length=2048)],
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def has_content(self):
        if self.ai_account == "chatgpt":
            if (
                not self.use_ai
                or not self.consent_external_ai
                or not self.consent_chatgpt_background
                or not self.chatgpt_connection_id
                or not self.text
                or not self.text.strip()
                or len(self.text.encode()) > 50000
                or self.source_url
                or self.image_id
                or self.source_id
                or not self.ai_destination
                or self.ai_destination[:2] != ("chatgpt", "https://api.openai.com/v1")
            ):
                raise ValueError(
                    "Personal ChatGPT imports require recipe text and explicit personal/background consent"
                )
        elif self.chatgpt_connection_id or self.consent_chatgpt_background:
            raise ValueError("Choose the personal ChatGPT connection explicitly")
        if not self.source_url and not self.text and not self.source_id and not self.image_id:
            raise ValueError("Provide a URL or source text")
        if self.source_id and self.image_id:
            raise ValueError("Choose one media source")
        if self.source_id and (not self.use_ai or not self.consent_external_ai):
            raise ValueError("Media extraction requires explicit AI consent")
        return self


class RecipeImportStatus(Model):
    id: UUID
    source_url: str | None
    source_platform: str
    state: Literal["queued", "preview", "needs_input", "confirmed", "cancelled"]
    recipe: Recipe | None
    extraction: ExtractionResult | None = None
    recognized_text: str | None = Field(default=None, max_length=100000)
    warnings: list[str]
    error_code: str | None
    confirmed_recipe_id: UUID | None
    created_at: float


class BringCredentials(Model):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


class BringConfiguration(Model):
    list_id: UUID


class PasswordChange(Model):
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=12, max_length=1024)


class HouseholdSettings(Model):
    name: str = Field(min_length=1, max_length=100)
    timezone: str
    language: Literal["en", "de"]

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value


class WeeklySuggestion(Meal):
    reasons: list[str] = Field(max_length=10)


class SuggestionPreview(Model):
    preview: Literal[True] = True
    monday: date
    basis: str = Field(pattern=r"^[a-f0-9]{64}$")
    meals: list[WeeklySuggestion] = Field(max_length=21)


class SuggestionApply(Model):
    request_id: UUID
    monday: date
    basis: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    checkpoint: SyncAnchor | None = None
    mutations: list[Mutation] = Field(min_length=1, max_length=21)


class SessionInfo(Model):
    id: UUID
    device_id: UUID
    access_expires: float
    refresh_expires: float
    revoked: Literal[0, 1]
    current: bool


class AdministrationStatus(Model):
    database_bytes: int
    media_bytes: int
    disk_free_bytes: int
    pending_jobs: int
    recipes: int


class JobInfo(Model):
    id: UUID
    kind: Literal["recipe.import", "shopping.reconcile", "bring.verify", "unknown"]
    state: Literal["queued", "running", "done", "failed"]
    attempts: int = Field(ge=0)
    error_code: str | None
    available_at: float


class JobCounts(Model):
    queued: int = Field(default=0, ge=0)
    running: int = Field(default=0, ge=0)
    done: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)


class ImportDiagnostic(Model):
    id: UUID
    state: Literal["queued", "preview", "needs_input", "confirmed", "cancelled", "unknown"]
    error_code: str | None
    created_at: float


class AdministrationDiagnostics(Model):
    captured_at: datetime
    job_counts: JobCounts
    recent_jobs: list[JobInfo] = Field(max_length=100)
    recent_imports: list[ImportDiagnostic] = Field(max_length=100)
