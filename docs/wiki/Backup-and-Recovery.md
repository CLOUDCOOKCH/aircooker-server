# Backup and recovery

Use portable household exports for moving household content, and protected volume
backups for full disaster recovery. Neither includes work that exists only on an
offline browser. Export that device's pending work separately before recovery.

| Backup type | Contains | Does not provide |
| --- | --- | --- |
| Household JSON/ZIP export | Household content, referenced photos, planning preferences and accepted-recipe counts | Password hashes, sessions, integration keys, notification subscriptions or a complete installation snapshot |
| Local SQLite snapshot | Consistent database, including password/session data and durable history | Separate photo files or configuration/encryption-key files |
| Stopped-volume backup | Database, media and configuration when the entire volume is included | Unsent edits on disconnected devices |
| Browser recovery export | That browser's records, drafts, outbox, archives and available photos | An automatically importable household archive or server credentials |

All of these can contain private household content. Restrict access and use encrypted
off-host storage. The application does not automatically encrypt a CLI database backup.

## Download a portable household export

1. Sign in to the administration console at `/`.
2. Open **Data** and download the ZIP household export.
3. Store it privately and record the server version that created it.
4. Test importing a copy into an isolated, compatible installation before relying on it.

The ZIP includes a versioned `manifest.json` and referenced `media/<UUID>.jpg` files
with checksums. JSON export is also available through the authenticated
`GET /api/v1/admin/export` API. The current household JSON format is version 3; ZIP
envelope version 1 embeds that manifest. Older compatible v1/v2 JSON remains importable.
Do not relabel an archive to bypass version checks.

## Import into another household

Configure and sign in to the destination first, then use **Data** to import the supported
JSON or ZIP file and confirm. This operation **merges** validated records transactionally.
Duplicate entity IDs reject the whole import with 409; existing data is not overwritten.
Destructive replacement is not implemented. Do not wipe an existing household to work
around a merge conflict.

Limits include 8 MiB JSON/manifest, 280 MiB ZIP, 10,000 entities, 5,000 media records
and the 256 MiB stored-photo quota. The proxy/CDN can have lower limits. Malformed members,
symlinks, mismatched checksums and unsupported archive encryption are rejected.
Reconfigure integrations and reconnect browser notifications after a clean household import.

## Create a consistent SQLite snapshot

Choose a new filename; the command refuses to overwrite an existing output:

```sh
docker compose -f compose.preview.yaml exec mealf python -m aircooker.cli backup --output /data/backups/household.sqlite3
```

For a source-build installation:

```sh
docker compose exec aircooker python -m aircooker.cli backup --output /data/backups/household.sqlite3
```

This uses SQLite's online backup API, so the database snapshot is consistent while the
server is running. The output file is mode 0600 and contains sensitive database state.
**Photo files and `/data/config` are separate and must be backed up as well.** A snapshot
inside the same volume will not protect you from losing that volume or host.

Never copy only an actively written `.sqlite3` file with an ordinary file-copy tool;
WAL writes may be outside it. For complete recovery, stop the backend and make a
protected backup of the entire local volume using your host's volume-backup tools.
Include `/data/config/integrations.key`, the encrypted settings/VAPID files, media and
database files together. Keep a private record of the matching image digest and Compose
configuration. Protect Cloudflare connector credentials separately from the MealF volume.

## Restore a complete volume

1. Preserve the current volume and stop all backend writers.
2. Restore the complete backup into a separate local volume with UID/GID 10001 ownership.
3. Start the matching application image against that volume, isolated from public traffic.
4. Verify health, household settings, recipes, photos and plans.
5. Use the interactive local [password recovery command](First-Run-Setup#recover-a-forgotten-password)
   to revoke restored sessions before public exposure.
6. Reopen public ingress only after verification, then sign devices in again.

Downgrading a migrated database is unsupported. To roll back an upgrade, restore the
matching pre-upgrade volume with its prior image. A lost encryption key prevents
decrypting saved integration and push credentials; restoring only the database is not
a complete recovery.

An older database can have a different history from a surviving browser. Preserve browser
recovery exports and use explicit history recovery; do not blindly retry old queues.
If the VAPID key changed, disconnect/reconnect notifications on each device. Test the
restoration process regularly; the existence of a backup file is not proof of recovery.

Source: [backup documentation](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/BACKUP.md)
and [local CLI implementation](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/src/aircooker/cli.py).
