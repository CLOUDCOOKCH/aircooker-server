# ADR 008 — durable device sign-out

Status: accepted for the development protocol, 2026-10-21.

A network request may rotate a refresh token while the device signs out. Clearing the
active token alone leaves a server session alive and allows a late response to restore
credentials. Offline sign-out also cannot honestly promise immediate server revocation.

Use an atomic, versioned Keychain envelope in the companion app: active credentials,
a generation identifier and pending revocation capabilities. Sign-out moves the active
refresh capability to the pending queue and changes the generation. Conditional refresh
and login writes cannot restore a prior generation. A late successful login is queued
for revocation. Library data and outgoing entity mutations are independent and preserved.

Add POST `/api/v1/auth/revoke` with the existing `Refresh` schema. The refresh secret
itself is the narrowly scoped authentication capability; no cookie, access token or session
UUID is accepted as authority. Current and retained rotated refresh hashes may revoke only
their associated session, including an expired session. Unknown/already-revoked secrets
produce the same empty 204 response. Rate limits and validation may return 429/422. Hashes
are looked up and revocation committed in one SQLite transaction; no new schema is needed.
An old refresh secret already revokes its session through existing replay detection, so
this endpoint provides an explicit idempotent operation without expanding that authority.

The app removes a pending capability only after an exact same-origin HTTPS 204 receipt.
It makes a bounded retry pass on launch/foreground/manual retry, without promising exact
background execution. An older server returning 404 leaves the queue pending; use the
administration console and upgrade. Secrets never enter SQLite, App Groups, logs or exports.
One app-owned vault actor per exact server service serialises read/apply/write operations.

Tradeoff: revocation capabilities stay in device-only Keychain while offline. They are
still secrets, although the pending queue is used only for revocation. A stolen refresh
secret must be treated as compromised. Immediate remote revocation needs connectivity;
users can revoke the device from another session in the administration console.

Evidence: backend tests cover current/expired/rotated secrets, independent devices,
idempotency, validation and rate limiting. Companion core tests cover durable envelopes,
legacy decoding, races, failed persistence/HTTP confirmation, HTTPS origin checks and
unchanged SQLite drafts/outbox identities. Keychain, UI and notification lifecycle still
require Apple SDK/device verification.
