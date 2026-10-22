import http.client
import ipaddress
import json
import re
import socket
import ssl
from decimal import Decimal
from html.parser import HTMLParser
from typing import NamedTuple
from urllib.parse import urljoin, urlsplit

from .errors import DomainError
from .ingredients import parse_ingredient
from .models import Recipe
from .recipe_extraction import RecipeTimes, RecipeYield, StepDetails

MAX_BYTES = 1_000_000


def public_address(address: str):
    ip = ipaddress.ip_address(address)
    if not ip.is_global or ip.is_multicast or ip.is_reserved:
        return False
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.sixtofour or ip.teredo:
            return False
        if ip.ipv4_mapped and not public_address(str(ip.ipv4_mapped)):
            return False
    return True


def public_addresses(host: str, port: int):
    try:
        addresses = {str(r[4][0]) for r in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)}
    except OSError as exc:
        raise DomainError("source_dns_failed", 422) from exc
    if not addresses or any(not public_address(a) for a in addresses):
        raise DomainError("source_address_forbidden", 422)
    return sorted(addresses)


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host, port=443, timeout=10, context=ssl.create_default_context())
        self.address = address
        self.tls_context = ssl.create_default_context()

    def connect(self):
        # Connect to the already validated address; TLS still verifies the original hostname.
        sock = socket.create_connection((self.address, 443), timeout=self.timeout)
        try:
            self.sock = self.tls_context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


class FetchedPage(NamedTuple):
    text: str
    url: str


def fetch_resource(url: str, content_types, max_bytes: int):
    for _ in range(4):
        try:
            parsed = urlsplit(url)
            parsed.port
        except ValueError as exc:
            raise DomainError("source_url_forbidden", 422) from exc
        if (
            len(url) > 2048
            or parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
        ):
            raise DomainError("source_url_forbidden", 422)
        addresses = public_addresses(parsed.hostname, 443)
        connection = PinnedHTTPS(parsed.hostname, addresses[0])
        try:
            connection.request(
                "GET",
                parsed.path + ("?" + parsed.query if parsed.query else "") or "/",
                headers={
                    "User-Agent": "mealf/0.1 recipe-import",
                    "Accept": ", ".join(sorted(content_types)),
                    "Accept-Encoding": "identity",
                },
            )
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                if not location:
                    raise DomainError("source_redirect_invalid", 422)
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise DomainError("source_unavailable_use_supplied_text", 422)
            media_type = response.getheader("Content-Type", "").split(";")[0].strip().lower()
            if media_type not in content_types:
                raise DomainError("source_content_type_unsupported", 422)
            if response.getheader("Content-Encoding", "identity") != "identity":
                raise DomainError("source_encoding_unsupported", 422)
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise DomainError("source_too_large", 422)
            return raw, media_type, url
        except (OSError, http.client.HTTPException) as exc:
            raise DomainError("source_network_failed", 422) from exc
        finally:
            connection.close()
    raise DomainError("source_redirect_limit", 422)


def fetch_page(url: str):
    raw, _, final_url = fetch_resource(url, {"text/html", "application/ld+json"}, MAX_BYTES)
    return FetchedPage(raw.decode("utf-8", errors="replace"), final_url)


def fetch_html(url: str):
    return fetch_page(url).text


class JSONLDParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.collecting = False
        self.parts = []
        self.documents = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
            self.collecting = True
            self.parts = []

    def handle_data(self, data):
        if self.collecting:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.collecting:
            self.documents.append("".join(self.parts))
            self.collecting = False


def find_recipe(value, depth=0):
    if depth > 20:
        return None
    if isinstance(value, dict):
        types = value.get("@type", [])
        if types == "Recipe" or isinstance(types, list) and "Recipe" in types:
            return value
        if "@graph" in value:
            return find_recipe(value["@graph"], depth + 1)
    elif isinstance(value, list):
        for item in value:
            found = find_recipe(item, depth + 1)
            if found:
                return found
    return None


def metadata_text(value):
    if isinstance(value, list):
        value = ", ".join(v for v in value if isinstance(v, str))
    return value[:5000] if isinstance(value, str) and value else None


def duration_minutes(value):
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", value)
    if not match or not any(match.groups()):
        return None
    days, hours, minutes, seconds = (int(v or 0) for v in match.groups())
    total = days * 1440 + hours * 60 + minutes
    return total if seconds == 0 and total <= 525600 else None


def extract(content: str, source_url=None, platform="website"):
    if len(content.encode()) > MAX_BYTES:
        raise DomainError("source_too_large", 422)
    parser = JSONLDParser()
    parser.feed(content)
    candidates = parser.documents or [content]
    found = None
    for doc in candidates[:50]:
        try:
            found = find_recipe(json.loads(doc))
        except (ValueError, RecursionError):
            continue
        if found:
            break
    if not found:
        raise DomainError("structured_recipe_not_found_use_manual_entry", 422)
    raw_ingredients = found.get("recipeIngredient", [])
    ingredients = [
        parse_ingredient(text)
        for text in (raw_ingredients[:300] if isinstance(raw_ingredients, list) else [])
        if isinstance(text, str) and text.strip()
    ]
    steps: list[str] = []
    details: list[StepDetails] = []

    def walk(value, depth=0, group=None):
        if depth > 10 or len(steps) >= 200:
            return
        if isinstance(value, str) and value.strip():
            steps.append(value[:5000])
            details.append(StepDetails(group=group))
        elif isinstance(value, dict):
            if "text" in value:
                walk(value["text"], depth + 1, group)
            elif "itemListElement" in value:
                walk(
                    value["itemListElement"], depth + 1, str(value.get("name", ""))[:5000] or group
                )
        elif isinstance(value, list):
            for child in value:
                walk(child, depth + 1, group)

    walk(found.get("recipeInstructions", []))
    servings = Decimal(2)
    raw = found.get("recipeYield")
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    stated_servings = False
    yield_info = None
    if isinstance(raw, str):
        serving_match = re.fullmatch(r"\s*(\d+)\s*(?:servings?|portions?|personen)?\s*", raw, re.I)
        yield_match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s+(.{1,100})", raw)
        if serving_match:
            raw = serving_match[1]
        elif yield_match:
            yield_info = RecipeYield(
                quantity=float(yield_match[1]), unit=yield_match[2], raw_text=raw[:5000]
            )
    try:
        servings = Decimal(str(raw))
        if not 0 < servings <= 1000000:
            servings = Decimal(2)
        else:
            stated_servings = True
    except Exception:
        pass
    recipe = Recipe(
        title=found.get("name", ""),
        description=str(found.get("description", ""))[:5000],
        source_url=source_url,
        source_platform=platform,
        ingredients=ingredients,
        steps=steps,
        instruction_details=details,
        servings=servings,
        yield_info=yield_info,
        times=RecipeTimes(
            prep_minutes=duration_minutes(found.get("prepTime")),
            cook_minutes=duration_minutes(found.get("cookTime")),
            total_minutes=duration_minutes(found.get("totalTime")),
        ),
        language=found.get("inLanguage") if isinstance(found.get("inLanguage"), str) else None,
        category=metadata_text(found.get("recipeCategory")),
        cuisine=metadata_text(found.get("recipeCuisine")),
        provenance={
            "extractor": "schema.org-jsonld",
            "quantities": "deterministic_requires_review",
            "ingredient_parser": "metric-en-de-v1",
            "servings": "source" if stated_servings else "default_requires_review",
        },
    )
    warnings = [
        "review_ingredient_quantities",
        "review_servings",
    ]
    if not isinstance(raw_ingredients, list) or any(
        not isinstance(text, str) or not text.strip() for text in raw_ingredients
    ):
        warnings.append("ingredient_entries_omitted")
    if isinstance(raw_ingredients, list) and (
        len(raw_ingredients) > 300
        or any(isinstance(text, str) and len(text.strip()) > 500 for text in raw_ingredients)
    ):
        warnings.append("ingredient_text_truncated")
    return recipe, warnings


def platform_for(url):
    try:
        host = (urlsplit(url).hostname or "").lower()
    except ValueError as exc:
        raise DomainError("source_url_forbidden", 422) from exc
    for domain, name in [
        ("instagram.com", "instagram"),
        ("tiktok.com", "tiktok"),
        ("youtube.com", "youtube"),
        ("youtu.be", "youtube"),
    ]:
        if host == domain or host.endswith("." + domain):
            return name
    return "website"


def _fetch_child(url, output):
    # Parsing/fetching a remote resource cannot monopolise the durable worker.
    # This process has no AI tools or access to credentials through its arguments.
    import resource
    import signal

    signal.alarm(25)
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    try:
        output.send(("ok", fetch_page(url)))
    except DomainError as exc:
        output.send(("error", exc.code))
    except Exception:
        output.send(("error", "source_fetch_failed"))
    finally:
        output.close()


def bounded_fetch_page(url: str):
    import multiprocessing

    context = multiprocessing.get_context("spawn")
    incoming, outgoing = context.Pipe(duplex=False)
    process = context.Process(target=_fetch_child, args=(url, outgoing), daemon=True)
    process.start()
    outgoing.close()
    try:
        if not incoming.poll(26):
            raise DomainError("source_timeout", 422)
        try:
            state, value = incoming.recv()
        except EOFError as exc:
            raise DomainError("source_resource_limit", 422) from exc
        if state != "ok":
            raise DomainError(value, 422)
        return value
    finally:
        incoming.close()
        process.join(timeout=1)
        if process.is_alive():
            process.terminate()
            process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join(timeout=1)


def bounded_fetch_html(url: str):
    return bounded_fetch_page(url).text
