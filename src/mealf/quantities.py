"""Bound decimal rendering before allocation; preserve stored/replayed representations."""

from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, Field

MAX_AMOUNT_LENGTH = 100
MAX_CALCULATED_LENGTH = 512
AMOUNT_DESCRIPTION = (
    "At most 100 characters in fixed decimal notation, ignoring insignificant trailing zeros."
)


def _renderable(value: Decimal, maximum: int) -> Decimal:
    if not value.is_finite():
        raise ValueError("Quantity must be finite")
    if value.is_zero():
        return Decimal(0)
    sign, digits, exponent = value.as_tuple()
    assert isinstance(exponent, int)
    # Do not use normalize(): it rounds to the active Decimal context precision.
    end = len(digits)
    while digits[end - 1] == 0:
        end -= 1
    exponent += len(digits) - end
    places = max(0, -exponent)
    whole = max(1, end + exponent)
    if sign + whole + (1 + places if places else 0) > maximum:
        raise ValueError("Quantity exceeds supported decimal length")
    return Decimal((sign, digits[:end], exponent))


def bounded_amount(value: Decimal) -> Decimal:
    _renderable(value, MAX_AMOUNT_LENGTH)
    # Sync receipts hash the original serialization, including trailing zeros.
    return value


def bounded_float_amount(value: float) -> float:
    bounded_amount(Decimal(str(value)))
    return value


def fixed_amount(value: Decimal) -> str:
    """Extra room for serving ratios/unit conversion, still bounded before format()."""
    return format(_renderable(value, MAX_CALCULATED_LENGTH), "f")


Quantity = Annotated[
    Decimal,
    Field(ge=0, le=1000000, description=AMOUNT_DESCRIPTION),
    AfterValidator(bounded_amount),
]
Positive = Annotated[
    Decimal,
    Field(gt=0, le=1000000, description=AMOUNT_DESCRIPTION),
    AfterValidator(bounded_amount),
]
IdeaServings = Annotated[
    Decimal,
    Field(gt=0, le=1000, description=AMOUNT_DESCRIPTION),
    AfterValidator(bounded_amount),
]
PlanningServings = Annotated[
    Decimal,
    Field(gt=0, le=100, description=AMOUNT_DESCRIPTION),
    AfterValidator(bounded_amount),
]
