# Changelog

## Unreleased — 0.1.0 development

Initial independently versioned repository. This is not a stable or production release.
See the implementation checklist for feature status and verification limits.

- Add authenticated immutable recipe photos, metadata stripping and storage quotas.
- Add media-aware JSON v2 / streamed ZIP exports and transactional validated restores,
  retaining historical references, tombstones and import provenance.
- Extend real-container E2E to image upload/replay/restart and both restore formats.
- Publish an additive OpenAPI contract for media; runtime dependency audit covers 34 packages.

- Preserve leftover reservation invariants on batch edits, deletion and discard; verify
  concurrent device reservations cannot spend the same portions twice.
- Add deterministic weekly suggestions using ratings, recent history, variety and available
  leftovers, with category/portion/repetition options and explicit reasons.
- Add snapshot-checked transactional live approval with durable replay receipts.
- Pin a canonical recommendation fixture shared with the independent native core tests.

- Add English/German administration controls for household settings, password changes,
  per-device revocation, Bring list configuration/retry and atomic JSON/ZIP import.
- Add encrypted AI settings with endpoint-bound key retention, environment override,
  redacted status, synthetic connection probes and persistent hourly request budgets.
- Exercise operational console workflows in real Chromium with explicit external-service
  doubles; configure a separate browser CI job and optional hashed tooling lock.
- Upgrade pytest to 9.0.3 to address the reported local temporary-directory advisory.

- Add immutable commit proofs, protected sync state reads and optional transactional anchor
  checks on pushes/pulls, including detection of reused revisions after a database restore.
- Add stable paginated history snapshots with tombstones and a soft response payload budget.
- Return delta/receipt proofs, retain ordinary restart compatibility, and publish a shared
  Python/Swift wire fixture for the pinned companion contract.

- Add idempotent device revocation using current or rotated refresh capabilities, with
  peer rate limits and no session-existence disclosure; retain Bearer logout compatibility.
- Verify revocation persistence in the real-container restart workflow.
- Make recipe use count outrank ratings/history when repeated weekly suggestions are allowed.

- Replace the administration accordion with dedicated sections and responsive navigation;
  refine typography, dark appearance, focus/controls and narrow/enlarged-text layouts.
- Preserve unsaved edits across section changes and retain existing secured workflows;
  update genuine Chromium captures and browser acceptance checks.
