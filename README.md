# aircooker-server

Self-hosted household meal planning, with an independent native iOS companion.
Apache-2.0. One process, one Docker container, SQLite and a persistent `/data` volume.
No mandatory hosted service, analytics or tracking.

**Development version. The complete product acceptance criteria are not yet met.**
The executable backend includes secure first-run setup, per-device sessions, versioned sync,
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
[Bring! integration](docs/BRING.md).

## Repositories

This folder is the root of an independent Git repository, intended for
`CLOUDCOOKCH/aircooker-server`. `aircooker-ios` is a separate sibling checkout, not a package
or submodule of this repository. No remote repository has been created or pushed.
The server owns [OpenAPI v1](contracts/openapi-v1.json); iOS pins an exact copy and SHA-256.

## Feature status

| Area | Current status |
| --- | --- |
| Bootstrap, Argon2id, per-device access/rotating refresh tokens | Implemented; automated tests |
| SQLite WAL, repeatable migrations, transactional mutation replay/tombstones | Implemented; automated tests |
| Recipes, meals, pantry, leftovers and saved template records | Implemented; automated tests cover key paths |
| Recurrences, serving scaling, pantry-aware aggregation | Implemented; bounded expansion and domain tests |
| Recommendations | Deterministic dinner previews; preference/history sophistication remains partial |
| Website recipe import | JSON-LD previews; ingredient parsing, images and broader HTML extraction remain partial |
| Social source imports | Source identification and public structured extraction; user text fallback; no authenticated fetching/transcripts |
| AI | Text adapters and validated output; simulated HTTP tests, no live verification |
| Bring! | SDK adapter, encrypted credentials, UUID ledger/reconciler and live probe; no live verification |
| Admin UI | English/German setup, login, jobs, summary and export; other configuration screens remain partial |
| Export/import | Versioned non-secret JSON and transactional merge; media/replacement workflow remains partial |
| Releases | Local development only; release CI is configuration, not proof of publication |

The project is independent and is not endorsed by Bring! Labs AG, Apple or any recipe source.
Use recipe text/images only when you have the necessary rights.
