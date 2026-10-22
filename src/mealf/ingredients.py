"""Conservative English/German quantity extraction; original text always survives."""

import re
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from .models import Ingredient

FRACTIONS = dict(
    zip(
        "¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞",
        (
            "1/4",
            "1/2",
            "3/4",
            "1/7",
            "1/9",
            "1/10",
            "1/3",
            "2/3",
            "1/5",
            "2/5",
            "3/5",
            "4/5",
            "1/6",
            "5/6",
            "1/8",
            "3/8",
            "5/8",
            "7/8",
        ),
        strict=True,
    )
)
NUMBER = r"(?:\d{1,6}\s+\d{1,6}/\d{1,6}|\d{1,6}/\d{1,6}|\d{1,7}(?:[.,]\d{1,6})?)"
LEADING = re.compile(rf"^({NUMBER})(?:\s*[-–—]\s*({NUMBER}))?\s*(.*)$")
UNITS = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "gramm": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "kilogramm": "kg",
    "mg": "mg",
    "ml": "ml",
    "cl": "cl",
    "dl": "dl",
    "l": "l",
    "liter": "l",
    "litre": "l",
    "litres": "l",
    "liters": "l",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "el": "tbsp",
    "esslöffel": "tbsp",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tl": "tsp",
    "teelöffel": "tsp",
    "cup": "cup",
    "cups": "cup",
    "piece": "piece",
    "pieces": "piece",
    "stück": "piece",
}
QUALIFIER = re.compile(r"^(.+?)\s+(to taste|as needed|nach Geschmack|nach Bedarf)$", re.I)


def quantity(text: str) -> Decimal:
    if "/" in text:
        parts = text.split()
        whole = Decimal(parts[0]) if len(parts) == 2 else Decimal(0)
        numerator, denominator = parts[-1].split("/")
        if Decimal(denominator) == 0:
            raise ValueError("Zero denominator")
        value = whole + Decimal(numerator) / Decimal(denominator)
    else:
        # A single group of three digits may be a thousands separator. Keep it
        # unparsed unless its leading zero makes decimal intent unambiguous.
        parts = re.split(r"[.,]", text)
        if len(parts) == 2 and len(parts[1]) == 3 and Decimal(parts[0]) != 0:
            raise ValueError("Ambiguous separator")
        value = Decimal(text.replace(",", "."))
    if not value.is_finite() or not 0 <= value <= 1_000_000:
        raise ValueError("Quantity outside supported bounds")
    return value


def parse_ingredient(text: str) -> Ingredient:
    original = text.strip()[:500]
    fallback = Ingredient(id=uuid4(), name=original[:200], original_text=original)
    normalised = original
    for character, fraction in FRACTIONS.items():
        normalised = normalised.replace(character, " " + fraction)
    normalised = " ".join(normalised.replace("⁄", "/").split())
    match = LEADING.fullmatch(normalised)
    if not match:
        qualifier = QUALIFIER.fullmatch(original)
        if qualifier:
            return fallback.model_copy(
                update={
                    "name": qualifier[1][:200],
                    "preparation": qualifier[2],
                }
            )
        return fallback
    try:
        amount = quantity(match[1])
        maximum = quantity(match[2]) if match[2] else None
        if maximum is not None and maximum < amount:
            return fallback
    except (InvalidOperation, ValueError, ZeroDivisionError):
        return fallback
    remainder = match[3].strip()
    if not remainder or not remainder[0].isalpha():
        return fallback
    first, _, rest = remainder.partition(" ")
    if re.search(r"[\d×/]", first):
        return fallback
    unit = UNITS.get(first.casefold().rstrip("."), "")
    if unit:
        remainder = rest.strip()
    # Packaging and qualified measures need review; never interpret pack size
    # as the total ingredient mass or turn a heaped spoon into an exact measure.
    elif first.casefold() in {
        "x",
        "heaped",
        "level",
        "gehäuft",
        "gestrichen",
        "oz",
        "lb",
        "lbs",
        "can",
        "cans",
        "tin",
        "tins",
        "dose",
        "dosen",
        "pack",
        "packet",
    }:
        return fallback
    if not remainder or not remainder[0].isalpha():
        return fallback
    name, separator, preparation = remainder.partition(",")
    if not name.strip():
        return fallback
    return Ingredient(
        id=fallback.id,
        name=name[:200],
        quantity=amount,
        quantity_max=maximum,
        unit=unit,
        preparation=preparation[:300] if separator else "",
        original_text=original,
    )
