# API and offline sync protocol v1

The canonical generated contract is `contracts/openapi-v1.json`. Generate with
`PYTHONPATH=src python scripts/export_contract.py`; CI checks exact drift. The live contract
is `/api/v1/openapi.json`. API-major 1 and sync-protocol 1 are exposed by system info.
The current contract describes implemented routes only. Missing operations remain on the
implementation checklist; the suggested product endpoint list is not falsely advertised.

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
`consent_external_ai=true`; the administrator selects endpoint, model and credential file.

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
