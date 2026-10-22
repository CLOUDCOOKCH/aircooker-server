# Recipe ideas error recovery verification

2026-10-22. Manual source/capture review: ship at the bounded error-recovery scope.
This is an implementation-agent review, not an independent specialist review or a live
Gemini, proxy, physical iPhone or whole-product acceptance result. No required UI fixes
remain in the inspected scope. Existing Mealf branding, palettes, typography and solid
form/glass navigation treatment are preserved. DESIGN.md and the PWA surface brief remain
the authorities; no tokens, layout system or original brand images changed.

The general failure alert previously hid nearly every persisted provider code. The PWA
now selects fixed English/German explanations and allowlisted diagnostic codes, keeps
unknown provider text out of the DOM, and provides a Settings route for terminal failures.
It opens Settings, where the AI section remains an existing expandable group. Inputs,
UUID replay, explicit consent/review/Save and no automatic paid retries are preserved.
Local storage/connectivity failures and expired requests have separate explanations.

The server distinguishes upstream 400/422 rejection, 404 model/endpoint absence and
blocked Gemini output. These categories do not assert the underlying provider-side cause.
Whitespace-containing Gemini display names are rejected before saving; model-ID help and
browser validation appear in PWA/admin. The administrator's non-JSON gateway fallback is
kept separate from a structured provider error. Existing valid model IDs are not rewritten.

## Evidence

- 435 backend tests pass, including durable provider failure/replay/redaction cases and
  display-name rejection without modifying saved configuration.
- 67 frontend tests pass, including safe localized error mapping and prototype-key/unknown
  text rejection. Frontend build/type checks and formatting pass.
- Ruff lint/format, mypy (50 source files), generated OpenAPI drift and git whitespace pass.
  No API schema, migration, database layout or native-repository change was required.
- Real Chromium recipe-ideas/SQLite/worker checks pass: three proposals, explicit reviewed
  offline Save/reload/sync, ingredient/surprise privacy, schema/model/quota failures,
  cached failure after reload without paid retry, Settings route and browser model-ID
  validity. Axe checks include the German desktop error state and existing proposal states;
  existing 320px flow and error-state viewport checks pass.
- Real Chromium administration checks pass, including HTML gateway fallback versus
  structured provider-code responses and browser model-ID validity. Provider HTTP and
  administration AI/Bring adapters are synthetic test doubles, not live-service evidence.

The implementation agent inspected desktop and phone errors together. Error text wraps
inside existing surfaces. A fixed phone navigation band appears over the full-document
capture at its original viewport position; the page remains scrollable and the Settings
recovery action is exercised by the browser check. Static captures do not prove motion
or screen-reader behavior. No launcher/detector or independent finish-agent pass is claimed;
the existing session context-loader failure was handled through direct project sources.

These genuine Chromium captures use synthetic household/provider data, German, After Dark.
They are product renders over synthetic provider HTTP, not fabricated UI mockups.

| Capture | Size context | SHA-256 |
| --- | --- | --- |
| [ideas-error-404-phone-de.png](../screenshots/recipe-ideas-errors/ideas-error-404-phone-de.png) | 390×844 viewport, full-page capture | `aa1f41e7e5cfaf6b846e23bb471870b111637c82b5e85eeb6725b84ff5f3f386` |
| [ideas-error-429-desktop-de.png](../screenshots/recipe-ideas-errors/ideas-error-429-desktop-de.png) | 1440×1000 viewport, full-page capture | `59fc3e08e0860113f85b3bc558ca24cdabeb6a971f798f24ae3a8f6c6429d4cd` |

## Deployment limit

The user reported an immediate `http_502` from the current administration connection test
and identified the model as “Gemini 3.8 Flash”. The exact saved ID, gateway response and live
provider cause remain unverified. The user was given the documented `gemini-3.8-flash` API
ID and Gemini v1beta base URL to check. Local fixes improve validation and diagnosis;
they do not establish that the user's deployment is repaired. No household credentials,
logs, keys, saved content or production endpoints were accessed or changed.

## Proxy-safe configuration validation follow-up

2026-10-22: user-supplied HTML confirms a Cloudflare error page. Older tunnel logs show
origin refusals outside that request's time; a current private health read succeeds.
Neither establishes the live AI error. No user HTML, addresses, ray IDs or raw logs are
committed here. The endpoint/UI fix is a tested diagnostic improvement, not live acceptance.

The existing AI test now maps known provider 5xx exceptions to HTTP 422 configuration
validation errors with allowlisted codes and a redacted `ai_connection_test_failed` log.
429 quotas, authentication, CSRF, ordinary server failures and success semantics remain
distinct; no test failure becomes a success. The worker/import/provider interfaces keep
their existing status/error behavior. Network connect/TLS/DNS failure gets a specific
`ai_connection_failed` code without claiming which cause occurred. Administration shows
fixed EN/DE recovery messages; genuine HTML gateway failures retain their separate hint.

445 backend tests and 67 frontend tests pass. Real API tests over actual provider adapters
and a 5xx-replacing proxy double preserve model, key, rejection, quota, timeout, transport
and malformed-response diagnostics, prove one provider call, close clients and redact
unknown error text/logs. Real Chromium administration validates the failed state and
EN/DE copy through a proxy double over the actual API, plus existing complete workflows.
Build/types, frontend format, Ruff lint/format, mypy and OpenAPI drift pass. Canonical API
schema is unchanged, so the existing native pin is deliberately retained. No migration,
credential, dependency, Docker runtime configuration or household data change is needed.

The implementation agent inspected these actual desktop/mobile captures together; no
required layout or copy defect remained at the bounded probe scope. Existing tokens,
form layout and navigation are preserved. A focused skip-link appears in the full-page
images; its keyboard behavior is incumbent. Provider, household and proxy data are
synthetic. No actual Cloudflare configuration, physical device or live provider was tested.

| Capture | Size context | SHA-256 |
| --- | --- | --- |
| [ai-probe-failed-desktop-en.png](../screenshots/recipe-ideas-errors/ai-probe-failed-desktop-en.png) | 1200×900 viewport, full-page capture | `f4b619496bf59542f440c0f15cf08fe2dbf170b04f8bd575c8b91109bfa677c0` |
| [ai-probe-failed-phone-de.png](../screenshots/recipe-ideas-errors/ai-probe-failed-phone-de.png) | 390×844 viewport, full-page capture | `7b9c63a88ea2e3d664bc88ec4a7f0695eb82d639f4f9daf3d4ddc2d7c7f5e6da` |
