"""Private, immutable and bounded import attachments. Never serve uploaded PDFs or videos."""

import hashlib
import re
import time
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

from pydantic import Field

from .errors import DomainError
from .media import MAX_UPLOAD_BYTES, normalise_image
from .models import Model

MAX_SOURCE_STORAGE = 128 * 1024 * 1024
SOURCE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "video/mp4",
    "video/webm",
}


class ImportSourceInfo(Model):
    id: UUID
    content_type: str
    byte_count: int = Field(gt=0, le=MAX_UPLOAD_BYTES)


def youtube_url(value: str):
    try:
        parsed = urlsplit(value)
        parsed.port
    except ValueError as exc:
        raise DomainError("video_url_unsupported", 422) from exc
    if (
        parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise DomainError("video_url_unsupported", 422)
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        video = parsed.path.removeprefix("/")
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/")):
            video = parsed.path.split("/")[-1]
        else:
            video = ""
    else:
        video = ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video):
        raise DomainError("video_url_unsupported", 422)
    return "https://www.youtube.com/watch?v=" + video


def put_source(database, source_id: UUID, raw: bytes, media_type: str):
    if media_type not in SOURCE_TYPES:
        raise DomainError("import_source_type_unsupported", 415)
    if not raw or len(raw) > MAX_UPLOAD_BYTES:
        raise DomainError("import_source_size_limit", 413)
    digest = hashlib.sha256(raw).hexdigest()
    with database.connect() as db:
        old = db.execute("SELECT * FROM import_source WHERE id=?", (str(source_id),)).fetchone()
    if old:
        if old["source_sha256"] != digest or (
            media_type.startswith("image/") is False and old["content_type"] != media_type
        ):
            raise DomainError("import_source_id_conflict", 409)
        return ImportSourceInfo(
            id=source_id, content_type=old["content_type"], byte_count=old["byte_count"]
        )
    data = raw
    if media_type.startswith("image/"):
        data, _, _ = normalise_image(raw, media_type)
        media_type = "image/jpeg"
    elif media_type == "application/pdf":
        if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-1024:]:
            raise DomainError("import_source_invalid", 422)
    elif media_type == "video/mp4":
        if len(raw) < 16 or raw[4:8] != b"ftyp":
            raise DomainError("import_source_invalid", 422)
    elif not raw.startswith(b"\x1a\x45\xdf\xa3") or b"webm" not in raw[:4096]:
        raise DomainError("import_source_invalid", 422)
    with database.transaction() as db:
        existing = db.execute(
            "SELECT * FROM import_source WHERE id=?", (str(source_id),)
        ).fetchone()
        if existing:
            if existing["source_sha256"] != digest:
                raise DomainError("import_source_id_conflict", 409)
            return ImportSourceInfo(
                id=source_id,
                content_type=existing["content_type"],
                byte_count=existing["byte_count"],
            )
        total = db.execute("SELECT COALESCE(SUM(byte_count),0) FROM import_source").fetchone()[0]
        if total + len(data) > MAX_SOURCE_STORAGE:
            raise DomainError("import_source_storage_limit", 409)
        db.execute(
            "INSERT INTO import_source VALUES (?,?,?,?,?,?)",
            (str(source_id), media_type, digest, len(data), data, time.time()),
        )
    return ImportSourceInfo(id=source_id, content_type=media_type, byte_count=len(data))
