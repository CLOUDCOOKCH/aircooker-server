# Export, backup and recovery

A household export is a versioned non-secret portable document or archive. A SQLite
recovery snapshot includes secrets and sessions. Both may contain private recipe content.

## Non-secret household export

The administration console downloads GET `/api/v1/admin/export/archive`. Its ZIP contains
`manifest.json` (`mealf-household-archive`, version 1) and `media/<UUID>.jpg` files with
SHA-256 metadata. It includes household name/timezone/language, typed entity snapshots,
retained deletion history, referenced photos, shared planning preferences and accepted-recipe counts. It excludes password hashes, active
sessions, integration credentials, keys, prompts, job internals and diagnostics.

GET `/api/v1/admin/export` provides JSON (`mealf-household`, version 3) with base64 media
for small exports. Version 1/2 JSON remains importable without the new preference/learning
fields. The ZIP envelope stays v1 and embeds the v3 household manifest; older server versions
cannot import it. Do not relabel archives to bypass compatibility checks. If JSON exceeds 8 MiB, use the archive.

On an already configured destination, POST JSON to `/api/v1/admin/import` or stream the ZIP
body to `/api/v1/admin/import/archive` with `Content-Type: application/zip`. Authenticate
with the destination household session. Browser mutations also require same-origin CSRF.
These endpoints merge; they never silently replace existing entities. Duplicate entity IDs
produce 409 and roll back media, entities, settings, planning preferences/learning and sync changes together. Validate the
result through the application and API before relying on a backup.

Archive restores reject unexpected/duplicate member names, symlinks, unsupported encryption,
invalid schemas, mismatched images/checksums and oversized content. They never extract ZIP
paths. Imported historical references can point to retained deleted recipes; tombstones
are applied after dependency restoration. Import provenance survives without old job data.

Limits: 10,000 entities, 5,000 media records, 8 MiB manifest/JSON, 280 MiB archive and a
256 MiB stored-photo quota. Transfers use protected `/data/jobs/.export-*.zip` and
`.restore-*.zip` files. Successful transfers clean up their files; interrupted process
termination can leave files. With the container stopped, administrators may remove only
these transfer files; never delete the durable job database. Startup-only stale transfer cleanup is implemented (RETENTION.md). General backup
retention and destructive replacement with explicit confirmation remain incomplete. Do not wipe an existing household to work around a merge conflict.

## Transactionally consistent sensitive backup

```sh
docker compose exec mealf python -m mealf.cli backup --output /data/backups/household.sqlite3
```

The output must not exist. SQLite's online backup API creates a consistent snapshot while
WAL writes continue. The staged copy passes quick/foreign-key checks and is atomically
published without overwriting an existing destination. Permissions are 0600. It includes database records, password hashes,
sessions, import data and ownership history. Recipe photo BLOBs are included in this SQLite snapshot. Configuration/encryption keys
and any separately stored files must also be backed up. Encrypt it before copying it off-host; this CLI
does not encrypt automatically and is explicitly a local administrator operation.

For complete recovery, stop the container and securely back up the entire local volume,
including configuration and integration encryption keys. Retain the matching image
version/digest. Never make an uncoordinated copy of an actively written SQLite database.

## Restore a volume

Stop all writers. Preserve the current volume. Restore a matching snapshot into a new local
volume owned by UID/GID 10001, keep it isolated from public traffic, start the matching image,
and verify DB health and household data. Revoke sessions using local recovery before public
exposure. Devices with cursors ahead of the restored server need controlled resync while
preserving pending changes. Test restoration regularly; an untested archive is not evidence.

## Device recovery after a database rollback

An ordinary container restart preserves commit proofs and does not require a device rebuild.
Restoring an older database can remove revisions or create a divergent branch after later
writes reuse revision numbers. The updated native client detects that with persistent commit
proofs before submitting its queued domain edits; pushes and pulls also check their anchors.
Older clients without these fields lack that protection. Update both pinned components.

After restore, device sessions may need sign-in again. In Settings → Sync and saved drafts,
review the recovery explanation and choose Rebuild from server. The app downloads a fixed
server snapshot into staging; interrupted downloads resume. On completion, all active local
cached records and their queued edits/deletions are archived on that device before the local
projection is replaced. Cached photos remain. Restoring an archived recipe makes a fresh UUID
and requeues available local media; it does not silently redirect old meal/template references.
Other archived record kinds remain available as text and require manual reconstruction.

These local archives are not in a server export or server backup, and cannot recover content
that was never cached on a surviving device. They are removed when the app is uninstalled.
No automatic history compaction/purge or destructive household replacement was added here.

Optional Web Push state is excluded from household JSON/ZIP transfer: reconnect each browser
after a clean import. A full protected volume recovery must preserve the SQLite database,
vault key and encrypted `/data/config/webpush-vapid.enc` together. If the public VAPID key
changes, the browser requires explicit disconnect/reconnect. Such volume copies contain
subscription/auth secrets and must remain private. See REMINDERS.md.

Maintenance prunes eligible terminal source/diagnostic data logically while retaining replay
proofs and offline media dependencies. It never deletes private backup files or household
exports. SQLite pages/WAL/volume snapshots can retain older data; see RETENTION.md.

## Offline household deletion

The installed local command `python -m mealf.cli delete-household` erases the current
household, sessions, recipes/media, sync history, jobs, setup state and saved integration
keys/credentials. It requires an interactive terminal, the exact `DELETE <instance UUID>`
confirmation and an exclusive volume lease. A running server or another deletion process
makes it refuse before changing data. Stop the service first; do not terminate individual
worker threads or edit database tables as a workaround.

For the preview service, run from the host in the **existing Compose project**:

```sh
docker compose stop mealf
docker compose run --rm --no-deps --entrypoint python mealf -m mealf.cli delete-household
docker compose up -d mealf
```

Use your existing Compose filename/flags and service (`mealf` in the source-build
example). The one-off container must use the same existing `/data` volume; creating a new
project/volume does not delete the original household. This command cannot run successfully
inside the ordinary still-running server container. NAS operators can run an equivalent
one-off container with the same image/volume and an interactive terminal after stopping
the server. Keep the normal non-root user and security settings.

Application-managed `/data/backups` is preserved by default and may still contain all
private household content. Add `--include-backups` only to explicitly erase those backups
too. External/off-host backups, snapshots, logs, environment-mounted keys, AI/Bring accounts
and already cached offline device data are unaffected. Remove or reconfigure those
separately if intended. No external Bring items are manipulated by deletion. File unlinking
is not a forensic erasure guarantee.

An interruption leaves a private `.household-deletion.json` marker and startup refuses to
serve a partial household. Resume the same command with the original backup choice; it
continues the same deletion rather than making a new household. Unexpected symlinked data
or malformed markers fail closed and require operator recovery. The lease and marker live
outside erased directories; normal shutdown keeps the lease until in-flight worker writes
finish. A hard process exit releases the OS lease, with SQLite/queue recovery on restart.

After completion, startup generates fresh setup credentials and a new household identity
on configuration. Old sessions are invalid. Offline clients retain their old household cache
and pending work; they cannot silently submit it to the new identity. Export needed local
work before deleting, and remove local device copies separately when desired.
