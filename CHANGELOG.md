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
