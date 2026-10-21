# API and offline sync protocol v1

The canonical generated contract is `contracts/openapi-v1.json`. Generate with
`PYTHONPATH=src python scripts/export_contract.py`; CI checks exact drift. The live contract
is `/api/v1/openapi.json`. API-major 1 and sync-protocol 1 are exposed by system info.
The current contract describes implemented routes only. Missing operations remain on the
implementation checklist; the suggested product endpoint list is not falsely advertised.

## Read-only administration diagnostics

Authenticated `GET /api/v1/admin/diagnostics?limit=20` returns a UTC capture timestamp,
queued/running/done/failed job totals and recent job/import status rows from one SQLite
read snapshot. `limit` applies separately to each recent list and must be between 1 and
100. This is a bounded recent view, not a complete audit-history export.

`GET /api/v1/admin/jobs` retains its list response and default limit of 100, now with a
typed schema, a validated `limit` and an optional `state=queued|running|done|failed` filter.
Rows sort by descending creation time and stable ID. Neither endpoint changes retries,
leases or stored imports. No job payload, imported recipe, source URL, external item name,
deduplication key or credential is returned. Only explicitly allowed public error codes
are exposed; unknown values become `operation_failed`, including syntactically valid
provider messages. Unknown job kinds and import states become `unknown`.

All protected endpoints accept `Authorization: Bearer <access token>`. Browser requests may
use the short-lived secure session cookie with CSRF protection. There is one household and
no account identifier accepted from the client. Never put credentials or setup tokens in a
URL or a QR code. The system identity/health/capabilities endpoints are public and omit secrets.

Resource create/update/delete requests use the same mutation envelope as sync. PATCH is an
atomic **complete replacement**, not a sparse patch. `payload` is a typed entity snapshot;
unknown fields are rejected. Numbers such as quantities are canonical decimal strings.
Lists paginate by stable UUID (`after`, `limit`), with `next` as the next-page key.

```json
{
  "mutations": [{
    "mutation_id": "00000000-0000-4000-8000-000000000001",
    "idempotency_key": "00000000-0000-4000-8000-000000000001",
    "entity_id": "1524cf77-c94c-487f-83ae-2c1fd26510e6",
    "kind": "recipe",
    "operation": "upsert",
    "base_revision": 0,
    "payload": {"title": "Soup", "servings": "2", "ingredients": [], "steps": ["Cook"]},
    "device_id": "0e548d0c-03ee-41b8-b5e7-ad7303b5ba7b",
    "client_timestamp": "2026-10-20T12:00:00Z"
  }]
}
```

Device ID must equal the authenticated session's device. Mutation ID and idempotency key
must be equal. Replay of an identical request returns the original result without another
change or external job. Reusing an ID with changed content returns 409. A push batch is
transactional; an invalid mutation rolls back the entire batch. At most 100 mutations may
be pushed at once. The current native engine sends individual ordered mutations.

`GET /api/v1/sync/pull?cursor=0&limit=100` returns `changes`, `cursor`, `has_more`.
Commit both local changes and cursor atomically. Pull again while `has_more`. If a cursor
is ahead of the server after a restore, preserve pending local content and request a
controlled resync; the current client surfaces the error instead of deleting local data.

Last saved change means last valid server commit, irrespective of device wall clocks.
A stale base sets `conflict=true`, but the write is accepted unless it violates a domain
invariant or tombstone. Any upsert against a deleted UUID returns `rejected_tombstone`.
The client preserves the draft; a recovery UI remains outstanding. IDs are never reused.

## Imports and AI

POST `/imports` with `request_id` (stable UUID), URL and/or source text returns a durable job.
Replaying the same ID/content returns the existing job. Different content for that ID is a
409. Poll `/imports/{id}`. A `preview` is not a saved recipe. Submit a reviewed recipe
mutation to `/imports/{id}/confirm`. Unsupported content returns `needs_input` with an error
code and retains its source URL. AI additionally requires `use_ai=true` and
`consent_external_ai=true`; the administrator selects endpoint, model and encrypted saved key or credential file.

## Weekly suggestion review

POST `/suggestions/weekly?monday=2026-10-19&seed=0` returns `preview=true`, canonical
Monday, snapshot `basis` and `meals` with reason codes. Optional repeated `categories`
query parameters select breakfast/lunch/dinner; `allow_repeats` defaults false; `servings`
can override recipe portions (positive, at most 100). Generation makes no calendar changes.

POST `/suggestions/apply` with `{request_id, monday, basis, mutations}`. Mutations are
ordinary complete meal mutations with new UUIDs and base revision zero; remove suggestion
`reasons` before constructing their payloads. At most 21 unique empty meal slots may be
approved. One transaction validates references/leftovers, applies all mutations and stores
the request receipt. `suggestion_preview_stale` or `suggestion_slot_occupied` returns 409
without changing the plan. Reuse the exact request UUID/body after response loss: the saved
results return even if the basis is now stale. Changed content/device at that ID conflicts.
This live API is distinct from iOS's locally atomic offline approval/outbox.

Leftover edits enforce booked portions, recipe and preparation-date invariants. A booked
batch deletion returns `leftover_in_use`; discard its unplanned availability instead.
See [planning semantics](PLANNING.md) and ADR 006 for detailed guarantees and limitations.

## Recipe photos

PUT `/api/v1/media/{image_id}` with multipart field `file` (JPEG/PNG/WebP, at most 8 MiB
source, 16 million pixels). Use a stable client-generated UUID and preserve source bytes
until acknowledgement. The server corrects orientation, drops metadata and stores a JPEG
at most 2048 pixels per edge / 1 MiB. It returns `MediaInfo`, including the canonical SHA-256.
Replaying original or canonical bytes returns the existing asset; different bytes at the
same UUID return `image_id_conflict` (409). Animated/invalid inputs fail with 422 and other
media types with 415. Metadata does not contain filesystem paths.

Authenticated GET `/media/{image_id}` returns JPEG bytes with ETag; `/info` returns metadata.
Missing assets return 404. Upload before submitting a recipe's `image_id`, or its mutation
fails with `recipe_image_not_found` (409). Assets are immutable and not deleted when an
image is replaced: offline references and retained history must remain valid. A 256 MiB
household quota returns `media_storage_limit` (409) without discarding existing records.
See [backup and restore](BACKUP.md) for JSON v2 and streamed archive endpoints.

## Errors and limits

Errors have `{ "error": { "code": "stable_machine_code" } }`. Submitted invalid values are
not echoed. 400 means invalid operation; 401 invalid/expired authentication; 403 permission,
CSRF or device mismatch; 404 missing entity; 409 state/replay conflict; 413 size limit;
422 schema/input failure; 429 rate limit; 502/503 integration failure. Validation details,
request IDs and Retry-After response headers need expansion before stable release.

Default access tokens last 15 minutes; refresh tokens rotate and expire after 30 days.
Replaying an old refresh token revokes that device session. Store refreshed credentials in
Keychain before retrying the request. Logout/recovery/password change must revoke sessions.
The admin console uses short-lived cookie access and requires login after expiration.

## Administration configuration

Authenticated GET `/admin/status` returns typed aggregate storage, recipe and pending-job
counts. GET `/auth/sessions` returns UUIDs, token expiries, integer `revoked` (0/1) and the
additive `current` flag; token hashes and secrets are excluded.

GET/PUT `/admin/ai` return redacted `AISettingsStatus`. PUT accepts complete settings;
`api_key=null` retains an existing key only for the same provider/base URL, while an empty
string clears it. `enabled=false` persists a disabled override. POST `/admin/ai/test` sends
fixed synthetic text, validates a recipe, and returns `validated_probe_response` with
`household_content_sent=false`. It shares the configured hourly budget and is also limited
to five probes per minute. No persistent live-verification guarantee is implied. See
[administration](ADMINISTRATION.md) for credentials, environment precedence and UI coverage.

## History proofs and full resynchronisation

The development contract extends sync protocol 1 with `sync_history_proof: 1` in capabilities.
GET `/sync/state?cursor=N` returns `{instance_id, cursor, token, requested_cursor,
requested_token}`. `cursor/token` identify the current head; `requested_token=null` means
that requested revision is absent. Revision zero always uses the sentinel `root`. Other
tokens are 32 lowercase hexadecimal characters, random per commit and persistent across
ordinary restarts. They are not credentials. Compare instance identity first, then the
last **observed** checkpoint, not merely a device clock or an integer cursor.

POST `/sync/push` accepts an optional `checkpoint: {cursor, token}` alongside `mutations`.
Its anchor is checked inside the write transaction. GET `/sync/pull` accepts optional `token`
for its requested cursor, checked in the same read transaction as the returned changes.
A mismatch returns `sync_history_changed` (409) without committing the batch. A valid older
anchor remains valid after later appends. New mutation receipts include `revision_token`;
legacy stored receipts can return null. Pull pages now include `cursor_token`. The native
client stores proof observations from preflights, receipts and deltas, including receipts
acknowledged before the next delta pull. Legacy clients omitting proofs do not gain restore
protection simply by upgrading the server.

GET `/sync/snapshot?cursor=N&token=T&limit=100&after=...` returns `{instance_id, checkpoint,
changes, next_after}`. Start at a current state anchor; omit `after` initially, then use the
returned value unchanged. It orders the latest snapshot of each `(kind, UUID)` at or before
that checkpoint, including deletions. Snapshot revisions are not globally ascending because
records are ordered by identity. `next_after=null` is the terminal page. Limits are 1–100
records, with a soft 2 MiB payload target; a single record is never split. A changed/missing
anchor returns 409. No session secrets, jobs or credentials enter snapshot payloads.

The native app stages pages without replacing its working library. Explicit recovery
confirmation authorises read-only continuation after interruption. Before replacing the
local projection, it rechecks the anchor and archives all active local records plus queued
deletions/updates transactionally. Previous outgoing work is retained in local drafts,
not replayed automatically. See ADR 007 and the companion SYNC_RECOVERY.md. Server history
compaction and device-archive import are not implemented.

## Offline-capable device sign-out

POST `/api/v1/auth/logout` still revokes the access-authenticated current session. The
additive POST `/api/v1/auth/revoke` instead accepts `{"refresh_token":"…"}` (`Refresh`
schema, 32–256 characters). The secret authorises only revocation of its own session;
current and retained rotated secrets work, so a refresh/logout race is recoverable.
It does not require or use a Bearer token or browser cookie. A session UUID alone has no
revocation authority. Unknown, expired and already-revoked capabilities return the same
empty **204**, preventing a session lookup oracle and permitting lost-response retries.
Invalid bodies return 422; more than 60 attempts per peer in five minutes return 429.

A client must persist the capability securely before removing active authentication and
retain it until an exact 204 receipt. A failed network request or an old server's 404 is
pending revocation, not success. Never retain refresh secrets in an entity mutation queue.
See ADR 008; this extension preserves API major/sync protocol 1/1.

## Optional per-device PWA notifications

`GET /api/v1/notifications/push` returns typed availability/public VAPID key, safe status and
preferences. `PUT .../subscription` registers validated endpoint/keys for the authenticated
device; `PUT .../preferences` applies times/category/language preferences; `DELETE
.../subscription` disconnects (204). `POST .../test` takes a UUID request_id and returns a
replay-safe typed queued response (202); `POST .../retry` returns the own-device requeued
count (202). Cookie mutations require CSRF/origin. Invalid input is 422, absent/disabled or
conflicting subscriptions are 409, expired auth 401 and per-device budgets 429. Credentials
are never returned. These additive v1 endpoints do not alter the retained native client
contract. REMINDERS.md specifies endpoint capabilities, privacy and delivery limitations.

## Household planning preferences

GET `/api/v1/household/planning-preferences` returns a typed revision/preferences/accepted_counts
snapshot for local scoring. PUT takes request_id/base_revision/preferences and returns a
typed request_id/revision/conflict receipt. Whole saves use server acceptance order; exact
device-bound replays return their old receipt without rewriting current state. Invalid input
422, reused IDs with changed payload/device 409, auth 401, cookie CSRF/origin 403 and write
budget 429. Existing preview query parameters override stored defaults when supplied.
`/suggestions/apply` learns only within its existing atomic successful approval transaction.
Household JSON export is v3; old v1/v2 imports remain supported without new metadata.
See PLANNING_PREFERENCES.md for wire/engine/backup behavior and limits.

## Recipe image imports

Use authenticated multipart `PUT /api/v1/media/{image_id}` with a stable client UUID,
then `POST /api/v1/imports` with the same optional `image_id` plus a stable `request_id`.
The request can carry corrected `text`; this skips OCR while retaining the source photo.
`use_ai` and `consent_external_ai` retain the existing text-only provider semantics.

`GET /api/v1/imports/{import_id}` has a typed response with optional bounded
`recognized_text` and an editable `recipe` preview. Nothing is added to the recipe
library before explicit confirmation. The canonical schema distinguishes recipe/ingredient
input and output serialization for decimal fields; wire field names are unchanged.
The companion native repository pins the reviewed exact contract bytes while retaining
its existing client UI. See [photo import](IMAGE_IMPORT.md) for error recovery and limits.
