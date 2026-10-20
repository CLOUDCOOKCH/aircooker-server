# Export, backup and recovery

Two different tools serve different needs. A household export is a versioned non-secret
portable data document. A SQLite disaster-recovery snapshot includes secrets and sessions.
Do not confuse them.

## Non-secret household export

Use the authenticated console Export action or GET `/api/v1/admin/export`. Format name is
`aircooker-household`, version 1. It contains household name/timezone/language and typed
active entity snapshots. It excludes password hashes, sessions, integration credentials,
keys, prompts, job internals and raw diagnostics. Treat recipe content as private even
though credentials are absent.

POST the document to `/api/v1/admin/import` on an already configured clean installation.
Imports validate schemas, order recipe/leftover/meal dependencies and commit atomically.
Duplicate IDs produce 409 and roll back the entire request; there is no silent overwrite.
The browser currently exports but has no import screen. Destructive replacement is not
implemented and must not be implied by the merge endpoint.

**Current limits:** media is not yet uploaded/exported; historical meals referring to a
deleted recipe need additional export treatment; exports over the 1.5 MB HTTP body limit
cannot be imported by this endpoint. Complete media-aware streaming export/import and
validated replacement with explicit confirmation are release blockers.

## Transactionally consistent sensitive backup

```sh
docker compose exec aircooker python -m aircooker.cli backup --output /data/backups/household.sqlite3
```

The output must not already exist. SQLite's online backup API makes the database consistent
while WAL writes continue. Permissions are 0600. This contains password hashes, sessions,
import data and ownership history. Encrypt it before copying it off-host; this CLI does not
automatically encrypt the output and is explicitly a local administrator operation.

For a complete disaster backup, stop the container and securely back up the entire local
volume, including media, the integration encryption key and encrypted credentials. Keep
the matching image digest/version. A cold volume snapshot avoids cross-file consistency
issues. Never use an uncoordinated copy of an actively written SQLite file as a backup.

## Restore a volume

Stop all writers. Preserve a copy of the current volume. Restore the complete matching
snapshot into a new local data volume owned by UID/GID 10001, keep it isolated from public
traffic, start the matching image, and verify DB health and household data. Revoke sessions
using local recovery before exposing a disaster-restored instance; restored tokens should
not remain trusted. Devices with cursors ahead of a restored server need controlled resync
while preserving their pending changes. Test restoration regularly; an untested archive
is not recovery evidence.
