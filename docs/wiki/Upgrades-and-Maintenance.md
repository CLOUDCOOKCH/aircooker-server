# Upgrades and maintenance

MealF is a development preview. Review the release notes and implementation status for
the exact image you are installing. Published-image checks apply to that image, not to
later source commits or every live external service.

## Update a preview installation

1. Finish active browser edits and synchronise devices where possible. Privately export
   pending work from devices that cannot sync.
2. Record the current image tag/digest, Compose files, environment and volume identity.
3. Create and verify a [complete pre-upgrade backup](Backup-and-Recovery).
4. In the existing installation directory, select the new reviewed `MEALF_IMAGE` in
   `.env`, or adopt the image reference from the chosen release's Compose file while
   preserving your settings and volume.
5. Pull first, then stop the old backend and start the new one:

   ```sh
   docker compose -f compose.preview.yaml pull
   docker compose -f compose.preview.yaml stop mealf
   docker compose -f compose.preview.yaml up -d
   docker compose -f compose.preview.yaml ps
   docker compose -f compose.preview.yaml logs --tail=100 mealf
   ```

If you use `compose.tunnel.yaml`, keep **both** `-f` arguments on these commands.
Keep your existing project name, `/data` volume, ingress and any intentional custom
port/command/healthcheck settings. Never start a second backend against the same volume.
Never use `down -v` for an upgrade.

For a source build, check out the intended revision, build it with `docker compose build`,
then stop `aircooker` and use `docker compose up -d` in the same project. Review any
Compose changes rather than replacing the deployment's configuration blindly.

## Verify after the update

Check the private and public health endpoints:

```sh
curl --fail http://127.0.0.1:8080/api/v1/system/health
curl --fail https://meals.example.com/api/v1/system/health
```

Replace the example hostname; the loopback check applies to the supplied port binding.
Both should report `{"status":"ok"}`. Inspect startup/migration errors, sign in and verify
the existing household, recipes, photos and calendar. Save a test change and confirm
it survives reload. Check integration/job status instead of assuming external writes
occurred merely because work was queued.

In the PWA, finish edits, accept the update prompt and reopen the app as needed.
Do not clear browser storage to update it. If setup unexpectedly appears, check the
volume mapping before creating a household. See [Troubleshooting](Troubleshooting).

## Roll back safely

A migration failure rolls back its transaction. Once a newer schema is committed,
downgrading that database is unsupported. Stop the new backend, preserve its current
volume, and restore the pre-upgrade volume snapshot with the prior matching image.
Verify it privately before returning traffic. Devices may need sign-in and explicit
history recovery after a database rollback.

## Routine health and diagnostics

The administration overview shows queue/import states, safe error codes, database/WAL
size, photo usage and free space. Authenticated read-only diagnostics are also available
at `/api/v1/admin/diagnostics` and `/api/v1/admin/jobs`. Do not share raw database dumps,
credentials, recipe sources or unredacted logs in issues.

Keep enough disk space for the database, WAL, photos, import sources, backups and
temporary archive transfers. SQLite file size does not immediately shrink after logical
cleanup. Do not delete WAL files, sync receipts or unreferenced photos by hand; an offline
device may still depend on them.

## Automatic and manual retention

The single backend worker runs bounded hourly cleanup. It preserves pending user work,
sync replay/history proofs, Bring! ownership and photos needed by offline edits.
Current source includes these conservative windows:

| Eligible data | Window / condition |
| --- | --- |
| Raw AI import uploads | After 7 days, unless referenced by queued/running import work |
| Confirmed/cancelled import previews and concluded source payloads | After 30 days, with stable replay receipts retained |
| AI attempt audit records | After 90 days |
| Eligible completed notification jobs | After 30 days; required receipts remain |
| Expired sessions without notification references | After 90 days past refresh expiry |
| Audit events | 90 days |
| Stale export/restore temporary files | Older than 24 hours, startup-only safe selection |

Inspect extra cleanup candidates locally:

```sh
docker compose -f compose.preview.yaml exec mealf python -m aircooker.cli cleanup --dry-run
```

Apply a bounded pass by removing `--dry-run`. For source builds use service `aircooker`
with the source Compose file. Output contains category counts. This is maintenance,
not full household deletion or guaranteed forensic erasure. Backups and exports have
their own operator-managed retention; the application does not delete them for you.

Source: [deployment](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/DEPLOYMENT.md),
[retention policy](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/RETENTION.md)
and [retention implementation](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/src/aircooker/retention.py).
