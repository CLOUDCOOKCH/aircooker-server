# ADR 013: bounded retention with persistent replay identities

Status: accepted implementation direction; broader storage/deletion work remains open.
Date: 2026-10-21.

Raw source text from finished imports need not live forever, but its request identity must.
Keep a canonical request fingerprint and terminal metadata; prune source jobs/preview payloads
after a completion grace period. Backfill known legacy shapes transactionally and retain
unknown data. Do not reconstruct or rewrite sync history. Confirmed imports are terminal even
if a late worker completes extraction afterward.

Use bounded hourly SQLite passes for old diagnostic/session/import/notification data.
Keep expired sessions with notification references and keep offline sync/Bring proofs intact.
Remove interrupted transfer ZIPs only at startup before requests, never under an active
transfer. Use standard-library/filesystem facilities; no scheduler container or new package.
Expose dry-run/apply through the existing local administrator CLI with redacted counts.

Reject age-only media deletion: an unreferenced upload may be an offline mutation dependency.
Full media/sync retirement and household deletion are separate, explicitly reviewed designs.
See RETENTION.md for exact retention windows, invariants, test evidence and physical-erasure
limits. No production/security/release acceptance is inferred from this maintenance slice.
