# Shopping requirements and manual Bring! sync

Open **Shopping list** in the desktop sidebar or **Shop** (**Einkauf** in German) in
the mobile navigation. Shortcuts on Home, Calendar and **Settings → Bring! → Shopping list**
open the same destination. This is a read-only view of mealf's calculated
requirements; the actual shopping experience remains inside Bring!.

The view shows the current household-local Monday–Sunday period, scaled/combined
quantities, pantry exclusions, last successful reconciliation and per-requirement status:
not sent, update pending, synced, purchased, manually removed, or a matching manual item
left unchanged. It includes only planned recipes, not every recipe in the library.
Existing leftovers do not add their recipe ingredients again. Different incompatible units
stay separate. Available pantry staples can be temporarily included from Pantry.

## Sync to Bring!

Select **Sync to Bring!** when connected and verified. mealf first sends this device's
pending edits to its server. If local changes remain blocked, it stops and explains why.
The server stores one deduplicated reconciliation job and processes it independently of
whether the app stays open. The button does not immediately claim success: polling shows
queued/running/errors and only committed ownership/reconciliation results become synced.
Automatic reconciliation after calendar changes remains enabled for verified connections.

A failed job can be retried manually, including during its retry backoff. Repeated presses
are guarded in the browser; server deduplication and persisted item UUIDs prevent duplicate
ownership. A job can fail after some items succeed: those item states remain visible rather
than claiming the entire list succeeded. State reflects the latest server reconciliation,
not an instantaneous live Bring! view. The current conservative purchased-item policy
suppresses the requirement for its week even if its requested quantity increases.

The last server calculation is cached in IndexedDB per household and remains viewable
after an offline reload. Offline/stale views say when they were calculated and warn that
new local edits may be missing. The sync button is disabled offline; the view does not
invent a fresh projection or send credentials from the browser.

## Lists load, but nothing gets added

List retrieval proves read access, not safe UUID-based writes. Earlier previews deliberately
required an operator-created compatibility report but did not expose the blocker clearly.
The shopping view now names that condition and offers a packaged verification flow:

1. Create/use a **dedicated disposable test list** in Bring!, select it in the administration
   console and return to Shopping list. Do not run the experiment on a normal household list.
2. Expand **Verify Bring! compatibility** and explicitly confirm this is a test list.
3. Select **Verify selected test list**. The durable worker adds one uniquely identified
   `mealf-test-…` item, repeats the add, updates its specification, completes it and removes it.
4. Only matching requested/returned UUIDs, expected states, and an unchanged baseline permit
   a passing report. Success queues ordinary reconciliation for that selected list.

The check never restores baseline items or removes an unidentified item by name. An API
that rewrites UUIDs fails closed; a temporary test item may need manual removal in Bring!.
A crash/network retry uses the same persisted test UUID/stage. Configuration changes stop
old attempts. Verification is limited to three new attempts per hour and only the server
holds the credentials. No container shell, secret files or Windows helper is required.

Evidence expires after 30 days and is bound to the exact credential/list configuration
and pinned bring-api SDK 1.1.2. The binding uses this server’s existing secret key; copying
evidence between installations cannot authorize writes. Changing accounts/lists or losing
write confirmation blocks writes until verification succeeds again. Older unbound reports need fresh verification;
never hand-write or edit an affirmative report. A test on one list does not authorize another.
If the live service cannot preserve item identities, automatic/manual mutations remain
disabled; use the displayed quantities to add items in Bring! manually. This unofficial
integration does not claim Bring! endorsement or guaranteed service compatibility.

## API and persistence

Authenticated `GET /api/v1/planning/shopping` is a typed, local database projection. It does
not call Bring! or return credentials. `POST /api/v1/integrations/bring/reconcile` queues a
manual current-week sync. `POST /api/v1/integrations/bring/verify` requires the selected
`list_id` and `dedicated_test_list_confirmed: true`; cookie requests use normal CSRF checks.
Verification and reconciliation run through the same single durable worker.

Migration 013 adds `shopping_sync` (latest successful period/list/manual-name snapshot) and
`bring_probe` (private configuration binding, test UUID/stage and baseline fingerprints).
Existing ledger, recipe, sync receipt and released migrations remain intact. Successful
ordinary writes now verify the returned UUID/state before ledger success. A mismatch clears
capability evidence. Portable household exports do not include integration credentials,
compatibility state or probe records; protected disaster-recovery volumes may contain them.
Probe history is currently retained conservatively; bounded retirement is later work.
The native repository and its contract pin remain deliberately unchanged by this additive
PWA/API extension.

## Evidence

The local real PWA/server/SQLite/worker acceptance covers explicit verification, failed and
successful manual sync, preservation of a manually added item, English desktop/German dark
phone/Axe and cached offline reload. Unit tests cover exact quantities/pantry/current-week
status, manual matching, purchased suppression, rate limits, changed configuration,
interrupted verification, rewritten UUIDs, unknown-item preservation and missing write
acknowledgements. Bring! HTTP behavior is synthetic; physical iPhone and live Bring!
compatibility remain unverified until separately recorded. See the bounded UI review and
release validation reports; preview publication is not production-v1 acceptance.

`poc-20261022.3` is published for AMD64/ARM64. All six exact-source CI jobs, fresh native
image scans/runtime checks, public asset/config identities, anonymous pull and the published
.2-to-.3 same-volume 5152 upgrade pass. The synthetic purchased ownership ledger and offline
replay survive; real EN/DE OCR remains preview-only and old ZIP/photo restore passes. See
[exact release evidence](validation/github-shopping-preview.json). This subsequent release
validation does not turn the manual UI review into a full accessibility or security audit.
