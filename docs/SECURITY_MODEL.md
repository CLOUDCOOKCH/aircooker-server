# Security model and initial threat analysis

This document is an engineering threat analysis, not a completed independent security audit.

Assets: household recipes/plans, account password, device sessions, AI and Bring credentials,
ownership ledger, SQLite durability and the Docker host's internal network.

Trust boundaries: public ingress → household API; app/extension shared files → native parser;
public recipe source → importer; optional AI response → recipe draft; Bring list → reconciler;
container → local persistent files. The Docker operator and a compromised host can access
household data and encryption keys and are trusted administrators. Shared-account users
have household-wide permission; this is not a multi-tenant role system.

| Threat | Implemented control | Remaining verification |
| --- | --- | --- |
| Remote first-run takeover | Random setup token in restricted file and operator-only startup log, atomic single-row creation, bootstrap rate limit | Concurrent-request acceptance test |
| Password guessing | Argon2id, persisted per-source and household rate limits, no default credentials | Resource/load testing |
| Stolen/replayed refresh | Opaque hashed tokens, expiry, rotation history, replay revokes that session | Device Keychain/expiry UI tests |
| Browser CSRF/XSS | HttpOnly Secure Strict cookies, CSRF double-submit + exact Origin, CSP, textContent, no remote scripts | Browser accessibility and session expiry workflows |
| Clock skew/duplicate sync | Transactional server sequence, fingerprinted replay, tombstones | Broader interrupted two-device end-to-end tests |
| Import SSRF/rebinding | Public HTTPS only, all DNS answers validated, pinned socket + hostname TLS, redirects rechecked | Exhaustive URL/IPv6/proxy tests |
| Oversized/parser inputs | HTTP cap, content cap, bounded structure traversal and job timeouts | Decompression/parser CPU and slow-read tests |
| Prompt injection | AI gets text only, no tools/execution/browsing, strict schema and mandatory preview | Provider-specific live refusal/truncation tests |
| Destructive Bring edits | UUID-only operations, no manual-item adoption, durable ledger and fail-closed capability gate | Dedicated-list live proof and concurrent-change testing |
| Credential leakage | Hashed sessions; encrypted Bring file separate from DB; AI key file; access logs disabled; redacted error codes | Complete dependency/log review |
| Backup disclosure | Non-secret export; local restricted sensitive-backup command | Encrypted automated backup/recovery workflow |

Network sources never use configured AI endpoints as fetch targets. Local AI HTTP is an
explicit operator opt-in; no import can select an internal address. DNS pinning still uses
normal TLS verification. CORS is not enabled; unrelated browser origins cannot read API
responses. Reverse proxy trust defaults empty, not universal.

The user explicitly requested the one-time bootstrap token in container startup logs.
Since POC `.3`, the server emits a `setup_required` JSON line with `setup_token` once per
unconfigured startup, using the current retained token. It never emits that line after
household setup, including with a stale token file. The token cannot bootstrap a configured
instance and its file is removed on success. Historical logs are not erased; log readers
are therefore trusted bootstrap administrators until setup completes. Operators can set
`LOG_SETUP_TOKEN=false` and use the restricted file instead. This narrowly scoped exception
does not cover account passwords, session/refresh tokens or provider credentials. Factory
construction/OpenAPI generation and ordinary HTTP requests do not emit the token.

Known open risks: request/body parsing still needs load and slow-client testing; there is no
complete retention policy; image/ZIP decoders need broader adversarial and load validation; filesystem privileges do not defend
against a malicious Docker administrator; integration service semantics remain unverified.
External integration configuration requires account-level authentication but the shared
account has no finer administrator role. A production readiness audit is still mandatory.

Device sign-out now has a capability-authenticated revocation endpoint (ADR 008). It
accepts refresh secrets, never unauthenticated session IDs, revokes only the associated
session and returns no session existence information. Retained rotation hashes close the
lost-refresh-response race. The iOS source keeps pending secrets in device-only Keychain
and rejects stale credential generations; native Keychain/lifecycle validation remains open.

## PWA trust boundaries

The public shell is hosted on the API origin under `/app/`. The service worker handles an
explicit public-build allowlist only; it never caches API/authenticated media responses.
Public demo art and application icons are labelled in the asset provenance file. Cookie
credentials are Secure, HttpOnly and SameSite=Strict, distinct from admin cookies. Unsafe
cookie requests require a matching CSRF token and exact configured origin. Refresh rotation
is serialised across open tabs with Web Locks where available. No long-lived password or
token is put in localStorage, IndexedDB, a manifest or QR code.

Private offline records/photos/drafts/outbox/archives stay in the origin's IndexedDB, separated
by backend instance UUID. This is not an encrypted native Keychain or biometric lock. Sign-out
revokes the browser session and hides, rather than deletes, cached work. Already cached data
cannot be remotely erased while a device is offline. Browser data eviction and shared unlocked
devices remain risks; request persistence, keep private exports and use device-level protection.

The server verifies history checkpoints for browser pushes, import confirmation and grouped
suggestion approval. Restored/forked history never silently drains an old queue. Explicit
snapshot recovery archives records/outbox before replacement. Blob image URLs are permitted
by CSP for locally validated JPEG/PNG; source strings/URLs are escaped and external attribution
links permit HTTP(S) only. No imported HTML or AI output is executed by the client.

Browser recovery exports include private content and photos, with no session/integration
secrets. They are separate from server household archives and require private handling.
Passkeys remain unimplemented. Optional Web Push uses device-authenticated/CSRF-protected
controls, encrypted subscription/VAPID credentials, an explicit vendor allowlist and public
DNS/socket pinning with verified TLS/no redirects. Generic payloads omit household content.
Consent, metadata exposure, replay/window/retry behavior, key recovery and live platform
limitations are documented in REMINDERS.md. No live vendor/device-delivery claim is made.
