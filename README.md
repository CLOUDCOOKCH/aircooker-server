# mealf server

**Mealf** is the product and package name. The administration console is at `/admin/`,
the PWA at `/app/`, and `/` is reserved for a separately hosted landing page.
Existing volumes and offline work are preserved; see [upgrade compatibility](docs/MEALF_MIGRATION.md).

**PWA-first delivery.** Open `/app/` on the configured HTTPS backend to use the primary
installable browser application. Home, Calendar, Recipes, Pantry, Settings, offline editing,
reviewed imports and two-device synchronisation have real Chromium acceptance coverage.
The native iOS repository is preserved for later. Read [install/use/develop the PWA](docs/PWA.md)
and [implemented/remaining scope](docs/PWA_IMPLEMENTATION.md). Choose Flo, After Dark or
Sunday in Settings; see [themes and offline appearance](docs/THEMES.md).
Use **Import recipe → Photo or screenshot** to take a recipe photo or choose an image,
extract English/German text locally and review it before saving. See
[photo import, privacy and limits](docs/IMAGE_IMPORT.md).
Optionally connect your personal ChatGPT plan for reviewed recipe-text imports using the
[Windows-friendly setup helper](docs/CHATGPT.md). Connections belong to an individual
browser session, not the household. Live subscription eligibility remains unverified.

Recipes without a usable picture show the original Mealf peach. URL imports, including
AI-assisted imports, try source recipe/preview images and retain them through review and
offline viewing. See [recipe photos and limits](docs/RECIPE_PHOTOS.md).

Open **Calendar → Shopping list** to inspect current-week quantities, Bring! item states
and failures, and use **Sync to Bring!**. See [shopping and safe verification](docs/SHOPPING.md).

Self-hosted household meal planning with a primary PWA and a retained native companion.
Apache-2.0. One process, one Docker container, SQLite and a persistent `/data` volume.
No mandatory hosted service, analytics or tracking.

**PWA v1 scope is frozen.** Production readiness, remaining engineering work and the
physical-device/live-service acceptance checklist are tracked in [v1 readiness](docs/V1_READINESS.md).
Preview publication does not imply stable acceptance.

For step-by-step operator guides, start with the [Wiki guide index](docs/WIKI.md):
installation, first-run setup, Cloudflare Tunnel, HTTPS, configuration, backups and recovery.
These maintained Wiki sources are prepared for publication in the separate GitHub Wiki.

**Development version. The complete product acceptance criteria are not yet met.**
The executable backend includes secure first-run setup, per-device sessions and durable sign-out support, versioned sync with restore-aware commit proofs,
recipe/calendar/pantry/leftover/template storage, bounded recurrence expansion, shopping
projections, a durable queue, structured recipe previews, optional text AI adapters, a Bring!
adapter, an administration console, and data export/import. See [status](docs/IMPLEMENTATION.md)
for partial features, test evidence and release blockers.

## Local development

Python 3.12 or newer:

For browser surfaces, first build with Node 24: `npm --prefix frontend ci`, then
`npm --prefix frontend run build`. Docker performs this automatically.
Source image-import development/tests also require Tesseract with English and German
language data; [installation and test guidance](docs/IMAGE_IMPORT.md#development-and-evidence).

```sh
python -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r requirements-dev.lock
pip install --no-deps -e .
export DATA_DIR="$PWD/data"
export BASE_URL=https://localhost
python -m mealf
```

The API binds port 8080. Use an HTTPS reverse proxy for browser login (cookies are always
Secure) and for all iOS connections. While unconfigured, each server startup prints a
`setup_required` log entry containing the one-time `setup_token`. It also remains in
`data/config/setup-token` until successful setup. Set `LOG_SETUP_TOKEN=false` to disable
this operator-requested bootstrap log entry.

```sh
python -m pytest -q
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m mypy src/mealf --ignore-missing-imports
PYTHONPATH=src python scripts/export_contract.py --check
```

## Docker

For the first prebuilt PWA preview, see [POC installation and limits](docs/POC.md) and
the [GitHub prereleases](https://github.com/CLOUDCOOKCH/aircooker-server/releases).
The source-build development path remains:

```sh
docker compose up --build -d
docker compose logs mealf
```

Open `/admin/` on the configured HTTPS origin and complete setup. The username and password must be
chosen by the administrator. There is no default account and no public registration after
setup. Configure `BASE_URL` before browser login. See [deployment](docs/DEPLOYMENT.md),
[security](docs/SECURITY_MODEL.md), [backup](docs/BACKUP.md), [API](docs/API.md) and
[Bring! integration](docs/BRING.md), and [administration](docs/ADMINISTRATION.md).

## Repositories

This folder is the root of the independent
[`mealf-server`](https://github.com/CLOUDCOOKCH/aircooker-server) repository.
[`mealf-ios`](https://github.com/CLOUDCOOKCH/aircooker-ios) is a separate companion,
not a package or submodule of this repository. Both development histories are published. Their actual remote names remain unchanged
until the owner renames them in GitHub Settings.
The server owns [OpenAPI v1](contracts/openapi-v1.json); iOS pins an exact copy and SHA-256.

## Feature status

| Area | Current status |
| --- | --- |
| PWA | Functional development client, genuine reviewed desktop/phone captures, 59 core tests and real Chromium/WebKit flows; physical Safari and remaining acceptance open |
| Brand artwork | Supplied original peach/wordmark installed in the PWA/console and install icons; [sources and compatibility](docs/BRANDING.md) |
| Bootstrap, Argon2id, per-device access/rotating refresh tokens | Implemented; automated tests |
| SQLite WAL, migrations, mutation replay/tombstones and restore history proofs | Implemented; automated tests; anchored snapshot recovery requires the updated native client |
| Recipes, photos, meals, pantry, leftovers and saved template records | Implemented; automated tests cover key paths |
| Recurrences, serving scaling, pantry-aware aggregation | Implemented; bounded expansion and domain tests |
| PWA reminders | Opt-in controls/offline drafts, durable scheduling/retries and real receiver with synthetic vendor tests; live delivery/iPhone unverified ([guide](docs/REMINDERS.md)) |
| Retention | Bounded hourly terminal-source/diagnostic/session cleanup, startup transfer cleanup and local dry-run CLI; sync/Bring/media proofs retained ([policy](docs/RETENTION.md)) |
| Recommendations | Local/server previews use ratings, history, variety and leftover reservations; atomic live approval and replay tested; shared defaults and bounded explicit-approval learning have offline/API/browser coverage ([guide](docs/PLANNING_PREFERENCES.md)) |
| Photo recipe import | Published in the current preview: real local EN/DE OCR, offline camera/image queue and explicit reviewed save; Chromium/WebKit CI and native container checks pass; physical camera unverified ([guide](docs/IMAGE_IMPORT.md)) |
| Website recipe import | JSON-LD previews and conservative metric/EN/DE fractions/ranges parsing; images and broader HTML extraction remain partial |
| Photo/screenshot recipe import | Camera/chooser, local EN/DE OCR, durable offline image queue and editable explicit-save previews; real Chromium tested, physical camera/iPhone unverified ([guide](docs/IMAGE_IMPORT.md)) |
| Social source imports | Source identification and public structured extraction; user text fallback; no authenticated fetching/transcripts |
| AI recipe import | Configurable Gemini (default), OpenAI, OpenRouter and compatible APIs; cloud vision for images/PDFs and supported Gemini videos, metadata-first websites, editable drafts and encrypted profiles ([guide](docs/wiki/AI-Recipe-Import.md)); live model compatibility unverified |
| Bring! | SDK adapter, encrypted credentials, UUID ledger/reconciler and live probe; no live verification |
| Admin UI | English/German setup, household, sessions/password, AI/Bring controls and JSON/ZIP transfer; Chromium tested; household deletion uses the tested offline operator CLI; extended diagnostics remain partial |
| Export/import | Media-aware JSON/streamed ZIP and transactional merge tested; destructive replacement remains incomplete |
| Releases | [POC 20261022.5 Mealf names/admin paths](https://github.com/CLOUDCOOKCH/aircooker-server/releases/tag/poc-20261022.5) published for AMD64/ARM64; exact-source CI, fresh scans/runtime/operator checks, public pull/assets and old-to-new 5152/PWA/offline/restore checks pass; stable acceptance remains open |

The project is independent and is not endorsed by Bring! Labs AG, Apple or any recipe source.
Use recipe text/images only when you have the necessary rights.

See genuine [PWA desktop](docs/screenshots/pwa-home-desktop.png),
[phone](docs/screenshots/pwa-home-phone.png) and [German dark calendar](docs/screenshots/pwa-calendar-phone-de-dark.png)
captures of the explicitly isolated demo. The food artwork is illustrative; the screens are
actual browser renders. Also see the genuine [console desktop capture](docs/screenshots/admin-desktop.png) and
[German phone capture](docs/screenshots/admin-mobile-de.png), using synthetic household data.
