"""Local, bounded OCR of validated recipe media; source facts always need review."""

import os
import re
import shutil
import subprocess
import tempfile
from decimal import Decimal
from functools import lru_cache

from .errors import DomainError
from .ingredients import parse_ingredient
from .models import Recipe

MAX_TEXT_BYTES = 100_000
OCR_TIMEOUT = 20


def process_environment():
    # OCR never needs provider credentials, network proxy settings or a shell.
    return {
        **{
            key: os.environ[key]
            for key in ("TESSDATA_PREFIX", "LANG", "LC_ALL")
            if key in os.environ
        },
        "OMP_THREAD_LIMIT": "1",
    }


@lru_cache(maxsize=1)
def ocr_available():
    binary = shutil.which("tesseract")
    if not binary:
        return False
    try:
        result = subprocess.run(
            [binary, "--list-langs"],
            capture_output=True,
            timeout=3,
            env=process_environment(),
            check=False,
        )
        return result.returncode == 0 and {b"eng", b"deu"}.issubset(result.stdout.splitlines())
    except (OSError, subprocess.TimeoutExpired):
        return False


def recognise_text(data: bytes):
    if not ocr_available():
        raise DomainError("image_ocr_unavailable", 503)
    binary = shutil.which("tesseract")
    if binary is None:
        raise DomainError("image_ocr_unavailable", 503)
    try:
        # The input has already passed bounded JPEG decoding/normalisation. A
        # temporary output file avoids buffering arbitrarily verbose OCR output.
        with tempfile.TemporaryFile() as output:
            result = subprocess.run(
                [binary, "stdin", "stdout", "-l", "eng+deu", "--psm", "3"],
                input=data,
                stdout=output,
                stderr=subprocess.DEVNULL,
                env=process_environment(),
                timeout=OCR_TIMEOUT,
                check=False,
            )
            if result.returncode:
                raise DomainError("image_ocr_failed", 422)
            output.seek(0)
            raw = output.read(MAX_TEXT_BYTES + 1)
    except subprocess.TimeoutExpired as exc:
        raise DomainError("image_ocr_timeout", 422) from exc
    except OSError as exc:
        raise DomainError("image_ocr_unavailable", 503) from exc
    if len(raw) > MAX_TEXT_BYTES:
        raise DomainError("image_text_too_large", 422)
    text = "".join(c for c in raw.decode("utf-8", errors="replace") if c in "\n\t" or ord(c) >= 32)
    if len(text.strip()) < 3:
        raise DomainError("image_no_readable_text", 422)
    return text.strip()


INGREDIENTS = re.compile(r"^(ingredients?|zutaten)(?:\s+(?:for|für)\s+.+)?\s*[:.]?$", re.I)
DIRECTIONS = re.compile(
    r"^(instructions?|directions?|method|preparation|steps|zubereitung|anleitung|zubereitungsschritte)\s*[:.]?$",
    re.I,
)
END = re.compile(
    r"^(nutrition|nutritional information|nährwerte|notes|notizen|tips|tipps|source|quelle)\s*[:.]?$",
    re.I,
)
SERVINGS = re.compile(
    r"(?:servings?|portions?|portionen|personen)\s*[:=]?\s*(\d+(?:[.,]\d+)?)|(\d+(?:[.,]\d+)?)\s*(?:servings?|portions?|portionen|personen)\b",
    re.I,
)


def printed_recipe(content: str, image_id, source_url=None):
    """Recognise explicit EN/DE sections; do not guess a recipe from a dish photo."""
    if len(content.encode()) > MAX_TEXT_BYTES:
        raise DomainError("image_text_too_large", 422)
    lines = [line.strip() for line in content.splitlines()]
    start = next((i for i, line in enumerate(lines) if INGREDIENTS.fullmatch(line)), None)
    end = next(
        (
            i
            for i, line in enumerate(lines)
            if DIRECTIONS.fullmatch(line) and start is not None and i > start
        ),
        None,
    )
    title = (
        next((line for line in lines[:start] if line and not SERVINGS.search(line)), "")
        if start is not None
        else ""
    )
    if start is None or end is None or not title or len(title) > 200:
        raise DomainError("image_recipe_layout_unclear", 422)
    ingredients = [
        parse_ingredient(re.sub(r"^[•*\-]\s+", "", line)) for line in lines[start + 1 : end] if line
    ]
    stop = next((i for i in range(end + 1, len(lines)) if END.fullmatch(lines[i])), len(lines))
    method = "\n".join(lines[end + 1 : stop]).strip()
    numbered = re.split(r"(?m)^\s*\d{1,3}[.)]\s+", method)
    if len(numbered) > 1:
        steps = [" ".join(part.split()) for part in numbered if part.strip()]
    else:
        paragraphs = re.split(r"\n\s*\n", method)
        steps = [" ".join(part.split()) for part in paragraphs if part.strip()]
    if not ingredients or not steps or len(ingredients) > 300 or len(steps) > 200:
        raise DomainError("image_recipe_layout_unclear", 422)
    match = SERVINGS.search("\n".join(lines[:end]))
    servings = (
        Decimal((match.group(1) or match.group(2)).replace(",", ".")) if match else Decimal(2)
    )
    recipe = Recipe(
        title=title,
        source_url=source_url,
        source_platform="image",
        image_id=image_id,
        ingredients=ingredients,
        steps=steps,
        servings=servings,
        provenance={
            "extractor": "local-image-ocr",
            "title": "first_line_requires_review",
            "ingredient_parser": "metric-en-de-v1",
            "servings": "source" if match else "default_requires_review",
            "review": "required",
        },
    )
    return recipe, ["image_text_requires_review", "review_ingredient_quantities", "review_servings"]
