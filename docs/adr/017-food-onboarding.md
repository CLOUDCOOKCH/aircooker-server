# ADR 017: Explicit pantry and shared taste onboarding

Status: accepted implementation, 2026-10-23; preview publication pending.

## Context

Households need a useful pantry starting point without invented stock, and Recipe ideas
needs durable taste input. Repeated household-AI import controls obscure the task. Preserve
existing entity sync, queued request identities, Bring! ownership, explicit recipe Save,
EN/DE and the approved Mealf visual system.

## Decision

Use one packaged EN/DE catalogue (`src/mealf/food_catalog.json`) for 24 pantry staples,
twelve taste cards and exact conservative pantry aliases. Save only chosen actual stock
as ordinary pantry entities. Show a dismissible fresh-household invitation; migration 016
marks existing households' pantry setup complete. Keep the picker reachable from Pantry.

Keep taste and setup flags in a separate revisioned shared profile API. IndexedDB stores
resumable drafts and device-bound outgoing writes; pantry edits and completion share a
local transaction. The server records request receipts transactionally, rejects mismatched
UUID replay, accepts stale bases with conflict information and applies changed fields in
server commit order. This avoids tying household settings to entity tombstones/history or
trusting device clocks. Lists replace a field rather than merge silently; overlapping
likes/dislikes fail validation.
A nonvisual follow-up preflights profile revision before queued PUTs and rejects backwards
history with `sync_history_changed`. Explicit server-history recovery archives raw food
state atomically with entities/outbox before clearing the active profile/queue; unfinished
setup drafts remain and old queued tastes do not replay automatically. Private local export
retains the archive.

Only an explicit Recipe ideas request sends a frozen preference snapshot to configured AI.
Old queued jobs keep their original body/fingerprint; later taste edits do not regenerate
or rebill them. Taste expresses preference, never an allergy constraint. Household imports
use concise disclosure plus an explicit Prepare AI preview action while preserving API
consent/destination pinning. Personal ChatGPT consent remains separate. Imports/proposals
still require review and explicit recipe Save.

Export household format v4 carries the non-secret profile and accepts formats 1–3. The
archive envelope stays v1. Replay receipts, browser drafts/outgoing queues and integration
secrets are not portable household-export fields; private pending-work recovery is separate.
The independent native companion pins its contract separately; no native onboarding UI is
introduced here.

## Consequences

Offline setup survives reload and sync and does not require provider access. Shared tastes
mean another device can overwrite the same field in commit order; this is documented rather
than silently treating the household account as individual users. Curated aliases avoid
broad food inference at the cost of leaving modified names unmatched. Taste requests can
contain personal household preferences, so disclosure and explicit generation consent must
remain visible. Existing pantry include-this-week and Bring ownership safeguards remain.
No new visual identity, raster artwork, font or broad token refresh is needed.

See [behavior and operations](../FOOD_SETUP.md), [API](../API.md#household-food-profile),
[backup](../BACKUP.md) and [review/evidence limits](../validation/food-setup-review.md).
