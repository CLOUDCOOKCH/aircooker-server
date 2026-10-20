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
| Remote first-run takeover | Restricted random setup-token file, atomic single-row creation, bootstrap rate limit | Concurrent-request acceptance test |
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

Known open risks: request/body parsing still needs load and slow-client testing; there is no
complete retention policy; media handling is absent; filesystem privileges do not defend
against a malicious Docker administrator; integration service semantics remain unverified.
External integration configuration requires account-level authentication but the shared
account has no finer administrator role. A production readiness audit is still mandatory.
