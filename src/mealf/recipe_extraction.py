"""Bounded, provider-neutral extraction DTO; model output never assigns stored identities."""

from decimal import Decimal
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from .quantities import AMOUNT_DESCRIPTION, bounded_float_amount

Text = Annotated[str, Field(min_length=1, max_length=5000)]
Amount = Annotated[
    float,
    Field(gt=0, le=1000000, strict=True, description=AMOUNT_DESCRIPTION),
    AfterValidator(bounded_float_amount),
]
Minutes = Annotated[int, Field(ge=0, le=525600, strict=True)]


class ExtractionModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
        allow_inf_nan=False,
    )


class RecipeTimes(ExtractionModel):
    prep_minutes: Minutes | None = None
    cook_minutes: Minutes | None = None
    total_minutes: Minutes | None = None


class ExtractedTimes(ExtractionModel):
    prep_minutes: Minutes | None
    cook_minutes: Minutes | None
    total_minutes: Minutes | None


class RecipeYield(ExtractionModel):
    quantity: Amount | None
    unit: Annotated[str, Field(min_length=1, max_length=100)] | None
    raw_text: Text | None


class ExtractedQuantity(ExtractionModel):
    value: Amount | None
    max_value: Amount | None
    unit: Annotated[str, Field(min_length=1, max_length=30)] | None
    raw_text: Annotated[str, Field(min_length=1, max_length=500)] | None

    @model_validator(mode="after")
    def valid_range(self):
        if self.max_value is not None and (self.value is None or self.max_value < self.value):
            raise ValueError("Invalid quantity range")
        return self


class ExtractedIngredient(ExtractionModel):
    name: Annotated[str, Field(min_length=1, max_length=200)] | None
    quantity: ExtractedQuantity
    preparation: Annotated[str, Field(min_length=1, max_length=300)] | None
    notes: Text | None
    optional: bool = Field(strict=True)
    group: Text | None
    original_text: Annotated[str, Field(min_length=1, max_length=500)] | None


class Temperature(ExtractionModel):
    value: Annotated[float, Field(ge=-273.15, le=2000, strict=True)]
    unit: Literal["C", "F"]


class StepDetails(ExtractionModel):
    group: Text | None = None
    duration_minutes: Minutes | None = None
    temperature: Temperature | None = None


class ExtractedInstruction(ExtractionModel):
    text: Text
    group: Text | None
    duration_minutes: Minutes | None
    temperature: Temperature | None


class RecipeContent(ExtractionModel):
    title: Annotated[str, Field(min_length=1, max_length=200)] | None
    description: Text | None
    language: (
        Annotated[str, Field(pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$", max_length=50)]
        | None
    )
    servings: Annotated[int, Field(ge=1, le=1000000, strict=True)] | None
    yield_info: RecipeYield | None = Field(alias="yield")
    times: ExtractedTimes
    ingredients: list[ExtractedIngredient] = Field(max_length=300)
    instructions: list[ExtractedInstruction] = Field(max_length=200)
    category: Text | None
    cuisine: Text | None
    tags: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(max_length=50)
    notes: Annotated[str, Field(min_length=1, max_length=10000)] | None

    @model_validator(mode="after")
    def unique_tags(self):
        if len(set(self.tags)) != len(self.tags):
            raise ValueError("Duplicate tags")
        return self


class ExtractionIssue(ExtractionModel):
    path: str = Field(max_length=500, pattern=r"^(?:/(?:[^~]|~[01])*)?$")
    message: Annotated[str, Field(min_length=1, max_length=1000)]
    severity: Literal["warning", "error"]


class ExtractionResult(ExtractionModel):
    schema_version: Literal["1.0.0"]
    recipe: RecipeContent
    issues: list[ExtractionIssue] = Field(max_length=100)

    @model_validator(mode="after")
    def missing_facts_need_review(self):
        checks = {
            "/title": (not self.recipe.title, "Recipe title is missing; enter it before saving."),
            "/servings": (
                self.recipe.servings is None,
                "Serving count is unknown; confirm it before saving.",
            ),
            "/ingredients": (
                not self.recipe.ingredients or any(not i.name for i in self.recipe.ingredients),
                "Review and name the ingredients before saving.",
            ),
            "/instructions": (
                not self.recipe.instructions,
                "Recipe instructions are missing; enter them before saving.",
            ),
        }
        required = [
            ExtractionIssue(path=path, message=message, severity="warning")
            for path, (missing, message) in checks.items()
            if missing and not any(i.path == path for i in self.issues)
        ]
        self.issues = required + self.issues[: 100 - len(required)]
        return self

    def reviewed_preview(self):
        """A complete compatibility preview, or null so the client can edit missing facts."""
        from .models import Ingredient, Recipe

        source = self.recipe
        if (
            not source.title
            or source.servings is None
            or any(not i.name for i in source.ingredients)
        ):
            return None
        return Recipe(
            title=source.title,
            description=source.description or "",
            servings=Decimal(source.servings),
            ingredients=[
                Ingredient(
                    id=uuid4(),
                    name=item.name or "",
                    quantity=Decimal(str(item.quantity.value))
                    if item.quantity.value is not None
                    else None,
                    quantity_max=Decimal(str(item.quantity.max_value))
                    if item.quantity.max_value is not None
                    else None,
                    unit=item.quantity.unit or "",
                    preparation=item.preparation or "",
                    original_text=item.original_text or "",
                    quantity_text=item.quantity.raw_text or "",
                    notes=item.notes or "",
                    optional=item.optional,
                    group=item.group,
                )
                for item in source.ingredients
            ],
            steps=[item.text for item in source.instructions],
            instruction_details=[
                StepDetails(**item.model_dump(exclude={"text"})) for item in source.instructions
            ],
            times=RecipeTimes(**source.times.model_dump()),
            language=source.language,
            yield_info=source.yield_info,
            category=source.category,
            cuisine=source.cuisine,
            tags=source.tags,
            notes=source.notes or "",
            provenance={"extractor": "ai", "review": "required"},
        )
