"""Bounded image decoding and immutable, transactionally backed recipe photos."""

import hashlib
import io
import warnings
from datetime import UTC, datetime
from uuid import UUID

from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import Field

from .errors import DomainError
from .models import Model

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_IMAGE_BYTES = 1024 * 1024
MAX_PIXELS = 16_000_000
MAX_EDGE = 2048
MAX_TOTAL_BYTES = 256 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class MediaInfo(Model):
    id: UUID
    content_type: str = "image/jpeg"
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(gt=0, le=MAX_IMAGE_BYTES)
    width: int = Field(gt=0, le=MAX_EDGE)
    height: int = Field(gt=0, le=MAX_EDGE)
    created_at: str


def info_for(row):
    return MediaInfo.model_validate({key: row[key] for key in MediaInfo.model_fields})


def normalise_image(raw: bytes, content_type: str):
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise DomainError("image_type_unsupported", 415)
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        raise DomainError("image_size_limit", 413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as image:
                expected = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
                if image.format != expected[content_type] or getattr(image, "n_frames", 1) != 1:
                    raise DomainError("image_type_mismatch_or_animated", 422)
                if image.width * image.height > MAX_PIXELS:
                    raise DomainError("image_pixel_limit", 422)
                image.load()
                # Honour orientation but discard EXIF/GPS, ICC and text metadata.
                oriented = ImageOps.exif_transpose(image)
                oriented.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
                if oriented.mode in ("RGBA", "LA") or "transparency" in oriented.info:
                    rgba = oriented.convert("RGBA")
                    clean = Image.new("RGB", rgba.size, "white")
                    clean.paste(rgba, mask=rgba.getchannel("A"))
                else:
                    clean = oriented.convert("RGB")
                # A fresh image strips metadata, including metadata inherited by convert().
                clean = Image.frombytes("RGB", clean.size, clean.tobytes())
                for _ in range(5):
                    output = io.BytesIO()
                    clean.save(output, format="JPEG", quality=85, optimize=True)
                    data = output.getvalue()
                    if len(data) <= MAX_IMAGE_BYTES:
                        return data, clean.width, clean.height
                    clean.thumbnail((int(clean.width * 0.75), int(clean.height * 0.75)))
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise DomainError("image_invalid", 422) from exc
    raise DomainError("image_size_limit", 413)


def validate_archived_image(data: bytes, info: MediaInfo):
    """Verify canonical exported JPEG without another lossy re-encoding on restore."""
    if len(data) != info.byte_count or hashlib.sha256(data).hexdigest() != info.sha256:
        raise DomainError("archive_image_checksum_mismatch", 422)
    if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise DomainError("archive_image_invalid", 422)
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "JPEG" or image.size != (info.width, info.height):
                raise DomainError("archive_image_invalid", 422)
            if (
                info.content_type != "image/jpeg"
                or image.getexif()
                or any(key in image.info for key in ("exif", "icc_profile", "comment"))
            ):
                raise DomainError("archive_image_metadata_forbidden", 422)
            image.load()
    except (OSError, ValueError) as exc:
        raise DomainError("archive_image_invalid", 422) from exc


def insert_media(db, info: MediaInfo, data: bytes, source_sha256: str | None = None):
    existing = db.execute("SELECT * FROM recipe_media WHERE id=?", (str(info.id),)).fetchone()
    if existing:
        if existing["sha256"] != info.sha256:
            raise DomainError("image_id_conflict", 409)
        return info_for(existing)
    total = db.execute("SELECT COALESCE(SUM(byte_count),0) FROM recipe_media").fetchone()[0]
    if total + len(data) > MAX_TOTAL_BYTES:
        raise DomainError("media_storage_limit", 409)
    db.execute(
        "INSERT INTO recipe_media VALUES (?,?,?,?,?,?,?,?,?)",
        (
            str(info.id),
            info.content_type,
            info.sha256,
            source_sha256 or info.sha256,
            len(data),
            info.width,
            info.height,
            data,
            info.created_at,
        ),
    )
    return info


def put_media(database, image_id: UUID, raw: bytes, content_type: str):
    # Retry the original bytes after a lost response without re-encoding the image.
    source_hash = hashlib.sha256(raw).hexdigest()
    with database.connect() as db:
        existing = db.execute("SELECT * FROM recipe_media WHERE id=?", (str(image_id),)).fetchone()
        if existing:
            if source_hash not in (existing["source_sha256"], existing["sha256"]):
                raise DomainError("image_id_conflict", 409)
            return info_for(existing)
    data, width, height = normalise_image(raw, content_type)
    info = MediaInfo(
        id=image_id,
        sha256=hashlib.sha256(data).hexdigest(),
        byte_count=len(data),
        width=width,
        height=height,
        created_at=datetime.now(UTC).isoformat(),
    )
    with database.transaction() as db:
        return insert_media(db, info, data, source_hash)
