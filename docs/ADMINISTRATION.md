# Administration console

Open the configured HTTPS `BASE_URL`. A fresh installation requires the one-time token
from `/data/config/setup-token`; there are no default credentials. After setup, sign in
with the shared household account. Browser access expires after 15 minutes and requires
sign-in again. Cookies are Secure/HttpOnly/SameSite=Strict; unsafe operations additionally
require the same Origin and CSRF token. No integration keys are stored in browser preferences.

English and German are available from the language selector. Changing the displayed
language preserves unsaved form fields. Household default language is saved separately.
Use the sidebar (a compact navigation grid on phones) to switch between Overview, Household,
Account, AI, Bring! and Data. Switching sections preserves unsaved fields; the selected
section is announced through the navigation state and page heading.

The dashboard shows the active recipe count, pending jobs, database/WAL size, stored photo
bytes, available volume space and recent job error codes. Counts cover the whole household.

## Household and access

Household settings save the name, validated IANA time zone and default language. Changing
the time zone changes calendar-week/shopping boundaries; inspect the plan after a change.
The account panel lists independent device sessions, expiry and revocation status. Revoke
individual devices, including the current session. Changing the password requires the
current password and revokes all sessions, including this browser. Local container recovery
is documented in DEPLOYMENT.md and also invalidates existing sessions.

## Optional AI

Select a provider, API base URL and model that your installation actually supports. Gemini
is the initial provider option; OpenAI, OpenRouter and custom OpenAI-compatible APIs also
support explicitly enabled model capabilities. Images/PDFs use compatible cloud models;
supported Gemini models additionally accept bounded video inputs. Legacy Anthropic, Ollama
and OpenWebUI adapters remain text-only. Enable formats and structured-output mode only
after checking that provider/model. See [AI Recipe Import](wiki/AI-Recipe-Import.md).

Settings saved in the console override environment settings. They are encrypted in
`/data/config/ai-provider.enc` using the restricted installation key. A saved disabled
configuration also overrides environment variables. Changing environment variables therefore
does not replace saved console settings. The API reports `origin` and any redacted
configuration error; it never returns a saved API key. Invalid environment settings can be
repaired from the console.

A saved profile is retained independently for each provider. Saving selects the default
provider/model; disabling AI retains profiles. A blank key field retains an existing key
only when the provider and base URL are unchanged (ignoring a final slash). Changing the
destination clears it unless a new key is supplied.
The remove-key checkbox explicitly clears it. Password/key inputs are cleared after their
operation. Do not place credentials in a base URL. HTTP requires explicit opt-in for a
trusted self-hosted AI service; public providers should use HTTPS.

Configure a timeout, maximum source size and installation-wide hourly request budget.
The budget is persisted in SQLite and shared by imports and connection probes. The probe
also has a five-per-minute limit. It sends only a fixed synthetic carrot-soup recipe and
validates the returned schema. It can incur provider charges. Successful probing does not
certify other models or future calls. Imports still require explicit consent before source
content is sent to the configured service. Keys and prompts are not exported or logged.

## Bring!

Save the account credentials, then connect to retrieve available existing lists. Saving
credentials alone does not authenticate them. Select a returned list and review its status.
The integration is unofficial. Automatic writes remain disabled until the dedicated-list
compatibility report proves the required UUID-based operations; the console cannot bypass
this gate. See BRING.md for the probe, supported capabilities and ownership safeguards.

Queue reconciliation to retry asynchronously and inspect job status afterward. Enqueued
work is not a claim that external shopping items changed. Disconnecting removes the saved
connection and preserves existing Bring! items. Live verification requires a dedicated test
account/list; development browser tests use an explicit connector test double.

## Export and import

Download a ZIP containing the versioned manifest and recipe photos. JSON exports remain
available through the documented API. Import a JSON or ZIP household export to merge it
transactionally. The console requests confirmation. Duplicate identifiers reject the whole
merge; existing records are not silently overwritten. Limits are 8 MiB for JSON and 280 MiB
for an archive. See BACKUP.md for media validation, volume recovery and secret exclusions.

Destructive replacement, account/data deletion controls, adjustable storage quotas and a
full diagnostic history are remaining work. An export is not a secret-bearing disaster
recovery backup.

Read-only diagnostics are available through authenticated `/api/v1/admin/diagnostics`
and the typed `/api/v1/admin/jobs` API. They expose bounded recent job/import states and
queue totals without content, URLs or provider messages. See API.md for limits and filters.
The overview displays queue totals and the 20 most recent jobs and imports, with localised
states, dates and useful error explanations. Hovering an error row exposes its redacted
diagnostic code; machine-readable details remain available through the API. Changing
language updates these rows without losing form edits. These endpoints do not retry or
mutate work. Complete audit-history browsing remains unfinished.

## Browser checks and screenshots

With Chromium or Chrome installed:

```sh
pip install --require-hashes -r requirements-browser.lock
pip install --no-deps -e .
python scripts/browser_smoke.py
```

Set `CHROMIUM_EXECUTABLE` for another installation path. `MEALF_SCREENSHOT_DIR` changes
the output directory (default `docs/screenshots`). The script runs a temporary loopback
server with synthetic household data and explicit test-only AI/Bring adapters. Production
still requires HTTPS. It exercises real browser forms, cookie/CSRF requests, household
editing, saved AI configuration/probe, Bring list selection/retry, JSON/ZIP transfer,
duplicate rejection, device revocation, password changes and EN/DE mobile layout. The
committed desktop/mobile screenshots are genuine Chromium renders of those fictional data.
The configured CI browser job has not been executed remotely.


The current presentation uses distinct settings pages, a persistent household identity,
light/dark appearances and a compact phone layout. Forms and requests retain the existing
cookie/CSRF protection; no security policy was relaxed for styling. Inputs retain 16px
base text, visible focus and contrasting boundaries. Browser checks exercise all six
sections at 320px with 200% root text size, one visible page/current navigation link and
no horizontal document overflow. That check uses a test-only intercepted same-origin
stylesheet, complying with the production content security policy.

Genuine captures: `admin-desktop.png`, `admin-desktop-dark.png`, `admin-mobile-de.png`,
`admin-mobile-settings-de.png`, `admin-mobile-ai-de.png` and `admin-setup.png`. Household
names and external integration inputs are synthetic; the AI and Bring services are doubles.
The captures show the actual running console. They are not native iOS screenshots.

Local administrators can inspect/apply a bounded retention pass with the packaged CLI
`python -m mealf.cli cleanup --dry-run` / `cleanup`. Hourly automatic passes preserve
pending work and replay identities; see RETENTION.md. No public deletion/cleanup endpoint
is introduced, and this is not full household data deletion.
