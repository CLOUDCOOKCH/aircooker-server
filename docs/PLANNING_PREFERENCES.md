# Household meal-suggestion preferences and learning

Settings → Meal suggestions controls categories (breakfast/lunch/dinner), repetition,
optional fixed portions and preference for available leftovers. Defaults remain dinner,
no repeated recipes, each recipe's own servings and leftovers enabled. This is a small set
of practical choices, not a dietary/medical model. No AI or external service is involved.

Choices are shared by the household after an explicit connected save. The PWA keeps a
validated snapshot for local offline scoring. Edits persist immediately as a separate local
draft through reload, even when incomplete; offline suggestions keep using the last saved
snapshot. Save online to apply the draft. The isolated demo applies choices only to its
own local database and never calls household APIs. Native code remains retained for later;
its old contract is not claimed to expose the new shared-settings UI.

On reopen/foreground/manual sync the PWA fetches the current shared snapshot and learned
counts. It does not repeatedly download the recipe database for recommendations. Another
device's saved choices appear after refresh/sync; a local unsaved draft is preserved rather
than overwritten. Pending preference/reminder drafts are included in the browser recovery
export's explicit `settings_drafts` allowlist; arbitrary local metadata is not exported.
This preserves them for manual recovery, not automatic reconstruction.

## Write order, replay and conflicts

GET/PUT `/api/v1/household/planning-preferences` are authenticated; cookie writes use existing
CSRF/origin controls and 120 writes/hour/device. PUT includes a UUID request ID, base revision
and a whole preference snapshot. SQLite serialises updates; the last server-accepted save
wins. The base revision reports whether another save intervened; device clocks do not choose
winners. Replaying an identical request returns its original receipt without changing the
current preferences or incrementing the revision. Reusing its ID with another device/payload
returns 409. The PWA retains the request ID while a failed save remains the same draft, and
fetches current state after saving. A delayed replay cannot overwrite a newer peer save.

This small settings snapshot is separate from the five sync entity kinds so retained native
v1 clients never receive an unknown entity kind. There is no secret or mandatory new service.
Preference drafts are explicit online saves, not silently queued settings mutations. Recipe,
meal, pantry and leftover offline queues retain their existing atomic sync protocol.

## Recommendations and learning

The PWA scores its actual cached library locally; the server offers its existing preview
endpoint. Saved defaults choose categories/portions/repetition/leftovers. Explicit older
preview query parameters still override categories/repeats/portions. Each engine preserves
occupied slots and reserved leftover portions, and combines rating/history with variety.
Without fixed portions, the local client may suggest the available remainder as one meal;
the server's existing preview uses the recipe's original servings when no override is given.
These are deliberate retained behaviors, not a claim of identical engine output.

Repetition is a strict count priority: all available recipes are used before a recipe is
repeated. A large learned score never defeats that priority. With repeats disabled, already
scheduled/suggested recipes are excluded from normal recipe candidates. Leftovers are a
separate preferred reuse case and never allocate more portions than remain. Disabling the
leftover preference excludes them from suggestions; it does not discard inventory/bookings.

Learning is deliberately simple: each successfully approved plan increments each distinct
chosen recipe once, even if it appears in several meal categories/days. The increment and
meal writes commit in the same transaction as the approval replay receipt. Duplicate delivery,
restart replay, failed/stale/occupied-slot approvals and ordinary manual meal edits do not
increment it again. A bounded positive bonus (at most ten score points) favors previously
accepted choices without overwhelming variety. Explanations disclose that a recipe was
chosen before. Acceptance never means the recipe was cooked; only explicit cooked history
counts as cooked history. No preference is inferred from private ingredients or assumed diets.

Learning begins with approvals committed by this implementation. Earlier approval receipts
are not reinterpreted or fabricated into history. Retained real scheduled/cooked meals still
influence existing history scoring. Counts are capped at one million per recipe; the current
context/export bounds are 10,000 recipes, aligned with export limits. Broader household quotas
and receipt/history cleanup remain release work; no unsafe automatic compaction is enabled.

Preview generation never writes meals. Users review recipe/category/portions/reasons and
explicitly approve their selection. Same-turn repeated activation is guarded synchronously;
selection, regeneration and dismissal are disabled during the local commit. Occupancy is
checked against current local persisted meals before saving. The server still checks its
current calendar atomically, because another device may have changed the plan. Existing
rejected grouped-approval recovery preserves the queued plan if such a conflict occurs.
A failure message tells users to check their calendar before regenerating; it does not claim
nothing was committed if a later local refresh failed.

## Portable export and restore

Household JSON is now format version **3**, including non-secret planning preferences and
accepted-recipe counts alongside entities/media. ZIP envelope version 1 embeds this v3
household manifest. Old v1/v2 JSON remains importable without the new fields, preserving
the destination's defaults; non-empty v3 metadata under an old version is rejected. Older server
versions cannot import v3; do not relabel an archive to bypass compatibility checks.

Restore validates count bounds and recipe references. Media, entities, preferences, counts,
settings and sync changes commit together or roll back. Duplicate entity imports remain
errors, never silently merged/replaced. Idempotency receipts, sessions, device notification
subscriptions and third-party credentials are excluded. A clean import receives a fresh
settings revision; there is no cross-installation device-clock authority.

## Evidence and remaining scope

Unit/API tests cover server order across devices, replay conflicts/restart, invalid inputs,
cookie CSRF, shared defaults/query overrides, actual leftover opt-out, bounded learning and
strict variety, approval replay/failure, preview freshness and v3/legacy restore rollback.
Web tests cover untrusted snapshots/drafts, multi-category local planning, leftovers/portions,
strict variety and durable allowlisted settings-draft export. The real Chromium flow covers
saved choices on two independent cookie sessions, offline draft/reload, last-saved offline
scoring, explicit 21-meal approval, once-only learning and same-turn double activation with
an assertion of exactly one 21-mutation approval group in IndexedDB. Axe checks cover the
stated settings/preview screens. Docker tests cover settings/learning restart and JSON/ZIP
restoration. Exact results and source/image/CI scope are in the validation reports.

No physical Safari/VoiceOver/OS-lifecycle acceptance, full dietary preference model, native
shared-settings UI, automatic archive reconstruction or complete product acceptance is
claimed. Original mealf artwork still requires the exact uploaded PNG files.
