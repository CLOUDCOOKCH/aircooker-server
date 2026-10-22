"""Best-effort source photos: trusted transport, untrusted metadata, local-only media."""

import json
from urllib.parse import urljoin, urlsplit

from .errors import DomainError
from .importing import FetchedPage, JSONLDParser, fetch_page, fetch_resource, find_recipe
from .media import ALLOWED_CONTENT_TYPES, MAX_UPLOAD_BYTES, normalise_image


class ImageMetadata(JSONLDParser):
    def __init__(self):
        super().__init__()
        self.previews = []

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        values = dict(attrs)
        key = (values.get("property") or values.get("name") or "").lower()
        if tag == "meta" and key in {"og:image", "og:image:secure_url", "twitter:image"}:
            if len(self.previews) < 20:
                self.previews.append(values.get("content", ""))


def image_candidates(page: FetchedPage):
    parser = ImageMetadata()
    parser.feed(page.text)
    images: list[str] = []

    def collect(value, depth=0):
        if depth > 5 or len(images) >= 20:
            return
        if isinstance(value, str):
            images.append(value)
        elif isinstance(value, dict):
            collect(value.get("contentUrl") or value.get("url"), depth + 1)
        elif isinstance(value, list):
            for child in value[:20]:
                collect(child, depth + 1)

    for document in (parser.documents or [page.text])[:50]:
        try:
            recipe = find_recipe(json.loads(document))
            if recipe:
                collect(recipe.get("image"))
                break
        except (ValueError, RecursionError):
            continue
    result = []
    for value in [*images, *parser.previews]:
        if not isinstance(value, str) or not value.strip() or len(value) > 2048:
            continue
        candidate = urljoin(page.url, value.strip())
        try:
            url = urlsplit(candidate)
            if (
                url.scheme != "https"
                or not url.hostname
                or url.username
                or url.password
                or url.port not in (None, 443)
                or len(candidate) > 2048
            ):
                continue
        except ValueError:
            continue
        if candidate not in result:
            result.append(candidate)
    return result[:3]


def source_photo(source_url: str, page: FetchedPage | None):
    page = page or fetch_page(source_url)
    for candidate in image_candidates(page):
        try:
            raw, content_type, final_url = fetch_resource(
                candidate, ALLOWED_CONTENT_TYPES, MAX_UPLOAD_BYTES
            )
            data, width, height = normalise_image(raw, content_type)
            return data, width, height, final_url
        except DomainError:
            continue
    return None


def _photo_child(source_url, page, output):
    import resource
    import signal

    signal.alarm(20)
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (384 * 1024 * 1024, 384 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    try:
        output.send(source_photo(source_url, page))
    except Exception:
        # Photo failure must never turn a successfully extracted recipe into a failed import.
        output.send(None)
    finally:
        output.close()


def bounded_source_photo(source_url: str, page: FetchedPage | None):
    import multiprocessing

    context = multiprocessing.get_context("spawn")
    incoming, outgoing = context.Pipe(duplex=False)
    process = context.Process(target=_photo_child, args=(source_url, page, outgoing), daemon=True)
    process.start()
    outgoing.close()
    try:
        if not incoming.poll(21):
            return None
        try:
            return incoming.recv()
        except EOFError:
            return None
    finally:
        incoming.close()
        process.join(timeout=1)
        if process.is_alive():
            process.terminate()
            process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join(timeout=1)
