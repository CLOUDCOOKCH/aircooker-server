# Configuration

MealF has two kinds of settings: container environment values controlled by the operator,
and household/integration settings saved through the application. Changing the container
time zone or an environment default does not overwrite saved household settings.

## Container settings

| Variable | Default | Configure it for |
| --- | --- | --- |
| `DATA_DIR` | `/data` | Persistent local state; keep the Docker volume mounted here |
| `BASE_URL` | `https://localhost` | Exact public HTTPS origin, with no application path |
| `TZ` | Image setting | Process time zone; household planning has its own saved IANA time zone |
| `TRUSTED_PROXY_CIDRS` | Empty | Actual ingress proxy peers; never universal trust |
| `LOG_LEVEL` | `info` | Server logging; avoid third-party debug logs that can disclose content |
| `LOG_SETUP_TOKEN` | `true` | Whether an unconfigured startup prints its one-time token |

For `compose.preview.yaml`, `.env` supplies `BASE_URL`, `TZ`, `TRUSTED_PROXY_CIDRS` and
the optional `MEALF_IMAGE`. `MEALF_IMAGE` selects the container image; it is a Compose
setting, not a backend variable. Add other backend variables under the service's
`environment:` section or an explicitly loaded Compose override. Putting an arbitrary
variable in `.env` does not automatically pass it into a container.

For the source-build `compose.yaml`, edit the literal environment values in that file
or use an explicit Compose override. After changes, use `docker compose ... up -d` with
the same files/project to recreate the container. A plain `restart` does not load changed
environment values. Preserve the volume and keep only one backend process.

## Household and account

At the administration console (`/admin/`):

- **Household** saves the name, IANA time zone and default language.
- **Account** lists device sessions and lets you revoke sessions or change the password.
- **AI** saves optional provider profiles and the selected default model.
- **Bring!** connects credentials and selects an existing list.
- **Data** downloads portable exports and imports compatible JSON/ZIP files.

The console is available in English and German. Its display-language selector is
separate from the saved household language. The shared household account has access to
these settings; there is no separate administrator-role system.

In the PWA (`/app/`), Settings also contains AI configuration, device display choices,
storage/sync recovery, household meal-suggestion preferences and per-device reminders.
Save shared preferences while connected. Reminder drafts remain local until explicitly
saved. See [PWA and offline use](PWA-and-Offline-Use) and [Meal reminders](Meal-Reminders).

## AI settings and precedence

The application can save Gemini, OpenAI, OpenRouter and custom OpenAI-compatible
profiles. Legacy text adapters for Anthropic, Ollama and OpenWebUI remain available.
Model names are administrator-supplied; no model version is guessed. Capabilities
must be enabled for the selected model. See [AI recipe import](AI-Recipe-Import).

Saved encrypted settings override AI environment settings. A saved **disabled** state
also overrides them. Changing `AI_MODEL` in Compose will therefore not replace a saved
profile. Inspect the reported configuration origin and edit the application setting.

| Optional AI variable | Default / meaning |
| --- | --- |
| `AI_PROVIDER` | Unset: disabled; supported provider identifier |
| `AI_BASE_URL` | Provider default; required for a custom compatible API |
| `AI_MODEL` | Required when AI is enabled; exact supported model ID |
| `AI_API_KEY_FILE` | Private regular key file readable by the backend; no group/world permissions or symlink |
| `AI_INPUT_FORMATS` | `text`; comma-separated supported capabilities, without spaces |
| `AI_TIMEOUT` | `30`; valid range 1–120 seconds |
| `AI_MAX_CONTENT` | `50000`; valid range 100–100000 UTF-8 bytes for text |
| `AI_REQUESTS_PER_HOUR` | `20`; valid range 1–1000, shared by imports and probes |
| `AI_STRUCTURED_OUTPUT` | `0`; set `1` only after verifying model/API JSON support |
| `AI_ALLOW_LOCAL_HTTP` | `0`; explicit opt-in for a trusted self-hosted HTTP API |

For key-file deployments, mount the file read-only with restrictive permissions that
permit UID 10001 to read it. Standard secret-file defaults may be too permissive for
this check. Do not put keys in an endpoint URL or recipe, and do not disable public TLS
verification. Application-managed keys are encrypted server-side and never returned to
the browser.

## Persistent state

| Path under `/data` | Purpose |
| --- | --- |
| `database/mealf.sqlite3` and WAL/SHM | Household records, sync history and durable jobs |
| `media/` | Recipe photos |
| `jobs/` | Protected temporary export/restore files |
| `backups/` | Operator-created local snapshots |
| `config/setup-token` | One-time bootstrap token, removed after setup |
| `config/integrations.key` | Installation encryption key; required to decrypt saved integrations |
| `config/ai-provider.enc` | Saved encrypted AI settings and profiles |
| `config/bring.enc` | Encrypted Bring! connection settings |
| `config/webpush-vapid.enc` | Encrypted installation Web Push private key |

Some files exist only after their feature is configured. Raw AI import sources are
private server state, separate from recipe photos, with bounded retention. Back up the
whole volume for disaster recovery; a household export intentionally excludes credentials.
Never delete encryption keys as a configuration-reset technique.

Source: [deployment](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/DEPLOYMENT.md),
[administration](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/ADMINISTRATION.md)
and [AI configuration implementation](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/src/mealf/ai_settings.py).
