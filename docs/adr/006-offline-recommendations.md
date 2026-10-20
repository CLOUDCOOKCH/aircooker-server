# ADR 006: Explicit leftover reservations and deterministic plan previews

Status: accepted for development, 2026-10-20.

A leftover record stores produced portions. Active meal references reserve portions,
including historical cooked records, so changing a date or marking a meal cooked does not
resurrect consumed food. Display unplanned availability as total minus reservations.
The native editor updates that availability in one actor-confined SQLite transaction.
Server writes also reject reductions, recipe changes or preparation dates that invalidate
bookings. Discard affects unplanned availability; reserved entries remain intact and can
still be edited without increasing portions. A booked batch cannot be deleted.

Use deterministic local scoring rather than mandatory AI for weekly recommendations.
Ratings, explicitly marked cooked history, recent scheduled history, current occurrences,
variety and available leftovers influence results. Each recipe is suggested once unless
repetition is enabled. Public and native engines share canonical fixture cases and a stable
seed tie-breaker. The tie-breaker is not a security mechanism. No freshness or nutritional
facts are inferred from dates or recipe names.

Approval is a separate mutation. Server live previews carry a SHA-256 snapshot basis;
transactional approval rejects stale or occupied slots and creates only new entries.
A durable device-scoped request receipt permits exact replay after response loss or restart.
Native offline previews compare their full local snapshot within the write transaction,
then persist selected meals and outgoing mutations together. Preferences remain device-local.

Consequences: receipts need a retention strategy that preserves replay safety; snapshots
can become conservatively stale after unrelated relevant-entity edits. Native sync still
submits individual mutations and does not use the live server preview receipt. Simultaneous
offline approvals may add multiple dishes to a slot rather than overwrite existing meals.
Cross-device batch/collision UX, shared household preferences, richer acceptance learning,
and Apple SDK lifecycle/a11y validation remain release work.
