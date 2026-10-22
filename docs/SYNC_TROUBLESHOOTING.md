# PWA synchronisation troubleshooting

Save open recipe/calendar editors before checking. Do not clear browser data, uninstall the
PWA, delete Docker volumes or reset household identity to diagnose a missing update.
**Settings → Export unsynchronised work** preserves a content-bearing recovery archive;
keep that file private. Normal server exports cannot include undelivered browser edits.

## Check the connection

Use **Sync now**, then open **Settings → Check sync connection**. Copy or export the report.
It includes local/server cursors, record counts, pending/blocked mutation counts, import
states, session/device and history-proof match booleans, the last successful complete run,
the last attempted phase and allowlisted errors. The report excludes recipe content, source
URLs, household/device/session IDs, history proofs, prompts, passwords and credentials.
It can be collected while sync is running or offline; failed probes remain visible.
The client bundle filename helps identify an old PWA. The API package version is not a
Docker image tag. Report collection does not clear the outbox or rebuild local storage.

| Observation | Meaning and next step |
| --- | --- |
| `history.cursor` exceeds `local.cursor` | Server changes remain to be downloaded. Retry; check proxy cache bypasses for `/api/*`. |
| `local_proof_matches: false` | History may have been restored/replaced. Export local work, then use the existing reviewed server-history recovery flow. |
| `identity_matches: false` | This URL reaches a different household installation. Confirm the server/volume before any recovery. |
| Session probe fails with 401 or device match is false | Use Settings → Sign in again. Retain local storage and the same device/outbox. |
| `origin_forbidden` / `csrf_failed` | Confirm `BASE_URL` exactly matches the public HTTPS origin and reverse-proxy routing; sign in again if required. |
| Pending/blocked mutations remain | Edits are still local. Resolve the shown rejection; do not report them as delivered. |
| Phase `imports` with a network error | Record sync runs first; the import still needs delivery/recovery. The queued source remains local. |
| `storage_unavailable` | Check Docker-volume space/permissions and configured SQLite limits, then retry the same pending mutations. |

Counts are a diagnostic clue, not a content comparison or permission to overwrite data.
Probes can span concurrent changes. Repeat after sync settles if counts differ. Bring! is
a separate backend integration: inspect Shopping list and its job/ownership status after
household changes have reached the server.

## Confirmed client defects and fix scope

Investigation on 2026-10-22 reproduced two sync-engine defects in the preceding source and
identified the misleading header selection:

- The header selected “Up to date” from an empty outbox even after an error, or before the
  initial check. Status now prioritises failure and starts as “Not checked yet”.
- A stale empty pull could return success despite a newer advertised server head or accepted
  write. Pull completion must now reach that known revision. Bounded incomplete catch-up is
  reported and resumes from committed pages. Fresh sync-read URLs/request cache directives
  resist ordinary URL-keyed proxy caches. A proxy explicitly ignoring query strings still
  needs `/api/*` cache exclusion; these protections do not certify proxy configuration.
- A failing queued import could abort all record exchange before it started. Durable outgoing
  changes and incoming pages now run before optional import delivery/polling. Import errors
  remain reported; queued sources and rejected edits are retained.

These are reproduced client bugs, **not a verified diagnosis of the user's deployment**.
The user reports missing updates with a synced indicator, but no deployed image, error
code or redacted report has yet been supplied. No live deployment was accessed or repaired.

## Evidence

Frontend regression tests cover old false-success conditions, interrupted catch-up and
resumption, stale proxy reads, import starvation, status precedence and report redaction.
The real-browser smoke `scripts/sync_status_browser_smoke.py` checks a real server/SQLite/
two independent cookie sessions: recipe/calendar/pantry delivery, offline Save/reload/replay,
expired-session rotation, failed/no-outbox status, stale-page rejection and copyable EN/DE
diagnostics. Only stale-page and 503 responses are injected test faults. The existing PWA
browser suite also covers concurrent edits, deletion/tombstone recovery and import review.
Desktop/390px Axe and 320px layout evidence do not establish physical-iPhone acceptance.

## Published update

`ghcr.io/cloudcookch/mealf-server:poc-20261022.8` contains these fixes. All six exact-source
CI jobs and fresh AMD64/ARM64 image security/runtime gates pass. Public assets, image
identities, anonymous pull and a disposable published .7-to-.8 same-volume upgrade on
internal port 5152 are verified; [exact evidence](validation/github-sync-preview.json).
Retain your volume and custom command/healthcheck. Save editors, accept the PWA update on
each device and retry Sync now. If updates remain missing, copy the connection report here
for diagnosis. Publishing this fix does not verify the cause on the user's installation.
