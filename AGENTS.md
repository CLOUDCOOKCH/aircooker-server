# mealf-server development guidance

Read README.md and docs/IMPLEMENTATION.md before work. Preserve the user's master product
requirements and maintain explicit tested/partial/unverified/blocked status.

The user explicitly authorises startup logging of the one-time bootstrap setup token while
unconfigured (default LOG_SETUP_TOKEN=true). This exception covers only that token, never
passwords, sessions or integration credentials. Configured starts must not emit it.

Use the existing checkout and Python/FastAPI modular monolith. Keep one SQLite writer
process, a durable queue, and API contracts owned by this repository. Protect transactional
sync, replay fingerprints, tombstones and Bring UUID ownership. Never silently enable
unverified external mutations or replace missing behaviour with fabricated content.

Use synthetic test data. Never commit real credentials, disable TLS verification, bypass
source access restrictions, or log household content and secrets. Keep Apache-2.0 compatible
dependencies. Released migrations are immutable.

Run pytest, Ruff check/format, mypy, and the generated OpenAPI drift check. Use the Docker
smoke test after persistence/deployment changes. Update the pinned iOS contract deliberately
in the independent companion repository. Do not claim Apple/live-service validation from
Linux or synthetic tests. Preserve the HIGH/CRITICAL container gate without suppressions;
record exact image, scanner and architecture evidence in validation.
