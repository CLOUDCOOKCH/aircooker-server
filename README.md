# mealf server

Formerly aircooker. The product name is **mealf**. Existing repository/package identifiers
remain compatible; see [branding and migration](docs/BRANDING.md).

**PWA-first delivery.** Open `/app/` on the configured HTTPS backend to use the primary
installable browser application. Home, Calendar, Recipes, Pantry, Settings, offline editing,
reviewed imports and two-device synchronisation have real Chromium acceptance coverage.
The native iOS repository is preserved for later. Read [install/use/develop the PWA](docs/PWA.md)
and [implemented/remaining scope](docs/PWA_IMPLEMENTATION.md).

Self-hosted household meal planning with a primary PWA and a retained native companion.
Apache-2.0. One process, one Docker container, SQLite and a persistent `/data` volume.
No mandatory hosted service, analytics or tracking.

**Development version. The complete product acceptance criteria are not yet met.**
The executable backend includes secure first-run setup, per-device sessions and durable sign-out support, versioned sync with restore-aware commit proofs,
recipe/calendar/pantry/leftover/template storage, bounded recurrence expansion, shopping
projections, a durable queue, structured recipe previews, optional text AI adapters, a Bring!
adapter, an administration console, and data export/import. See [status](docs/IMPLEMENTATION.md)
for partial features, test evidence and release blockers.

## Local development

Python 3.12 or newer:

```sh
python -m venv .venv
. .venv/bin/activate
pip install --require-hashes -r requirements-dev.lock
pip install --no-deps -e .
export DATA_DIR="$PWD/data"
export BASE_URL=https://localhost
python -m aircooker
```

The API binds port 8080. Use an HTTPS reverse proxy for browser login (cookies are always
Secure) and for all iOS connections. Read the one-time setup token from
`data/config/setup-token`; it is not logged and disappears after successful setup.

```sh
python -m pytest -q
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m mypy src/aircooker --ignore-missing-imports
PYTHONPATH=src python scripts/export_contract.py --check
```

## Docker

```sh
docker compose up --build -d
docker compose exec aircooker cat /data/config/setup-token
```

Open the configured HTTPS public URL and complete setup. The username and password must be
chosen by the administrator. There is no default account and no public registration after
setup. Configure `BASE_URL` before browser login. See [deployment](docs/DEPLOYMENT.md),
[security](docs/SECURITY_MODEL.md), [backup](docs/BACKUP.md), [API](docs/API.md) and
[Bring! integration](docs/BRING.md), and [administration](docs/ADMINISTRATION.md).

## Repositories

This folder is the root of the independent
[`CLOUDCOOKCH/aircooker-server`](https://github.com/CLOUDCOOKCH/aircooker-server) repository.
[`aircooker-ios`](https://github.com/CLOUDCOOKCH/aircooker-ios) is a separate companion,
not a package or submodule of this repository. Both development histories are published.
The server owns [OpenAPI v1](contracts/openapi-v1.json); iOS pins an exact copy and SHA-256.

## Feature status

| Area | Current status |
| --- | --- |
| PWA | Functional development client, genuine reviewed desktop/phone captures, 32 offline/planning/sync tests and real Chromium flows; physical Safari and remaining features open |
| Bootstrap, Argon2id, per-device access/rotating refresh tokens | Implemented; automated tests |
| SQLite WAL, migrations, mutation replay/tombstones and restore history proofs | Implemented; automated tests; anchored snapshot recovery requires the updated native client |
| Recipes, photos, meals, pantry, leftovers and saved template records | Implemented; automated tests cover key paths |
| Recurrences, serving scaling, pantry-aware aggregation | Implemented; bounded expansion and domain tests |
| Recommendations | Local/server previews use ratings, history, variety and leftover reservations; atomic live approval and replay tested; shared preference learning remains partial |
| Website recipe import | JSON-LD previews and conservative metric/EN/DE fractions/ranges parsing; images and broader HTML extraction remain partial |
| Social source imports | Source identification and public structured extraction; user text fallback; no authenticated fetching/transcripts |
| AI | Encrypted admin configuration, bounded text adapters and synthetic probe tests; no live verification |
| Bring! | SDK adapter, encrypted credentials, UUID ledger/reconciler and live probe; no live verification |
| Admin UI | English/German setup, household, sessions/password, AI/Bring controls and JSON/ZIP transfer; Chromium tested; deletion/extended diagnostics remain partial |
| Export/import | Media-aware JSON/streamed ZIP and transactional merge tested; destructive replacement remains incomplete |
| Releases | Local development only; release CI is configuration, not proof of publication |

The project is independent and is not endorsed by Bring! Labs AG, Apple or any recipe source.
Use recipe text/images only when you have the necessary rights.

See genuine [PWA desktop](docs/screenshots/pwa-home-desktop.png),
[phone](docs/screenshots/pwa-home-phone.png) and [German dark calendar](docs/screenshots/pwa-calendar-phone-de-dark.png)
captures of the explicitly isolated demo. The food artwork is illustrative; the screens are
actual browser renders. Also see the genuine [console desktop capture](docs/screenshots/admin-desktop.png) and
[German phone capture](docs/screenshots/admin-mobile-de.png), using synthetic household data.
