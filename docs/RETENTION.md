# Conservative retention and maintenance

The backend makes bounded hourly database maintenance passes and removes stale temporary
archive transfers at startup before serving requests. No extra service or scheduled host
command is required. Maintenance uses server timestamps, not device clocks. Fixed policy:

| Data | Policy |
| --- | --- |
| Confirmed/cancelled import previews and source jobs | After 30 days from terminal state, clear the extraction preview/warnings/error and remove concluded source jobs only when a stable request fingerprint is retained |
| Unreviewed/needs-input/queued imports | Keep their content; never expire pending user work automatically |
| Unknown legacy import receipt | Keep its source job/preview rather than guess a replay identity |
| Finished notification jobs | After 30 days, remove accepted meal jobs with retained delivery receipts, or finished orphan jobs whose subscription was explicitly removed; keep active-subscription test request receipts and failed/queued/running work |
| Expired sessions | After 90 days past refresh expiry, remove only sessions with no notification-subscription reference; remove their obsolete refresh history in the same transaction; keep device identities |
| Audit events | Retain 90 days |
| Expired rate-limit buckets | Retain at least 24 hours after reset time; current buckets remain intact |
| Interrupted export/restore ZIP files | At startup only, remove regular `.export-*.zip`/`.restore-*.zip` files older than 24 hours from `/data/jobs`; skip symlinks/directories/recent files and unrelated names |

Each database category is limited to 500 candidates per pass; large backlogs drain over
subsequent passes. Cleanup failures emit only a redacted `maintenance_cleanup_failed` event
and do not stop the durable job worker. Successful non-empty passes log counts, not source
text, paths, credentials or household content. The next hourly pass retries maintenance.
Startup file pruning follows the supported single application process; do not run multiple
servers against one data volume. Runtime cleanup does not unlink active transfer files.

Raw AI import uploads are separately eligible after 7 days unless an import draft still
references them in queued state (including while its worker runs). AI attempt audit records
are eligible after 90 days. Both use the same bounded hourly maintenance and dry-run CLI.
Saved recipes and pending draft content are not deleted by this source-upload cleanup.

## Local administrator inspection

Inside the existing container:

```sh
docker compose exec aircooker python -m aircooker.cli cleanup --dry-run
docker compose exec aircooker python -m aircooker.cli cleanup
```

Both return JSON category counts. Dry run does not prune rows. Repeating apply is safe;
zero candidates is a normal result. The command uses the same installed application version
and SQLite transactions as the server and can run while that server is active. It does not
remove transfer files while the server is serving requests. Use a private volume backup
before manual database operations; this tool is not a full data-deletion command.

## Import replay and upgrade invariants

Migration 009 adds a canonical SHA-256 receipt over the already validated source text/URL,
AI flag and disclosure consent, plus a terminal timestamp. New imports write it immediately.
Existing jobs backfill in 100-row batches inside the migration transaction. Unknown legacy
shapes retain a null fingerprint and remain exempt from pruning. Existing terminal jobs
receive a fresh 30-day completion grace period because their old completion time is unknown.
A failure rolls back columns/data/indexes and the migration marker; repeat startup does not
extend the grace period or rewrite sync history.

After pruning, replay of an identical import request still returns its original final state.
Changed source/flags under the same UUID still return an idempotency conflict. Confirmation
mutation receipts, imported recipe identity/provenance and ordinary offline editing remain
valid. The confirmed/cancelled draft's minimal record, source attribution and fingerprint
remain retained; internal retention fields are not added to the client import response.
An explicitly saved recipe stays intact. Its old extraction preview is not a second recipe
archive. A retried/late worker cannot downgrade a confirmed import to preview or needs-input.

## Deliberately retained data

Cleanup does not purge canonical entity tombstones, change-log commit proofs, mutation
receipts, grouped suggestion/preference replay receipts, accepted-recipe history, Bring!
ownership or purchase history. These may still be needed by a long-offline device or to
avoid recreating an external requirement. Referenced notification preferences/receipts and
their session link remain available for explicit reconnect/disconnect.

Recipe media also stays retained. An upload that is not yet referenced on the server can
belong to an offline device's pending recipe mutation. Deleting it merely because no current
server recipe points to it would lose work. The existing image quota remains enforced;
safe media compaction and bounded sync-history retirement require a separately verified
resynchronisation/active-device protocol. Backups, user exports and arbitrary config files
are not cleanup targets.

This is logical application pruning, not a forensic erasure guarantee. SQLite can reuse
freed pages without immediately shrinking its files; WAL/volume snapshots and backups may
retain earlier data. Keep sensitive backups private. Explicit offline household deletion is now available (BACKUP.md). Safe media/sync-history
compaction, broader quotas and full volume recovery remain separate engineering work.

## Evidence

Tests cover terminal-source pruning with identical/changed import replay, confirmation replay
and later recipe editing, unchanged sync proofs, pending/unknown legacy preservation,
bounded/dry-run passes, session/refresh/device references, notification purchase-independent
delivery receipts/test replay, safe startup file selection, multi-batch upgrade backfill,
migration rollback and restart idempotency, confirmed-worker races and redacted maintenance
failure with an ordinary job still processed. Packaged CLI dry-run/apply are exercised in the
non-root/read-only Docker smoke. Full ordinary PWA/console regressions still run. Exact
counts, image IDs, source/CI and remaining limits are in the retention validation reports.

## Database growth and unavailable storage

`DATABASE_MAX_BYTES` defaults to 2 GiB (2147483648); configure 1 MiB–64 GiB as an integer.
Every SQLite connection enforces the main-file page cap. It does not cap WAL, temporary
transfers, container logs or separately retained backups: monitor free space on the whole
volume and retain operational headroom. An existing larger database is never truncated;
SQLite caps it at its current page count until the administrator raises the setting.

Quota/disk/I/O failure returns a redacted 503 `storage_unavailable`. The entire failed
mutation rolls back with no success receipt; the PWA keeps its exact mutation and photos
pending across restart. Increase the configured cap or recover host storage, then retry.
Do not delete sync history, the database or browser storage to work around the cap. A
large tombstone update can itself need space; freeing/recovering operator-managed storage
or raising the limit may be necessary before application deletions can complete.

Transient storage failures while claiming or finishing a job no longer terminate the sole
worker. It logs only `worker_retry`, backs off and retries; existing lease/fencing/replay
rules still apply. Real SQLite-full tests verify rollback, history integrity and identical
mutation retry, plus reconnect/restart cap enforcement and worker recovery. This does not
claim disk-controller fault injection, long-running load or a complete retention/GC policy.
