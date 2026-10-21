# Changelog

- Publish the first mealf PWA POC (`poc-20261021.1`) to GHCR for AMD64/ARM64, with exact-source
  CI gating, fresh image scans/runtime tests, SBOMs, provenance and a preview Compose file.
  Verify public anonymous pull and E2E against the published image; retain stable-release gates.

- Add bounded conservative retention and a dry-run/apply administrator CLI. Persist import
  request fingerprints before pruning terminal source/preview payloads; keep pending work,
  replay/sync/Bring proofs and offline media dependencies. Clean stale archive transfers
  at startup, preserve session references, and prevent late workers downgrading confirmation.

- Add shared suggestion categories/portions/repeats/leftover choices with durable offline
  drafts and cached local scoring. Learn only from successful explicit approvals, with
  replay-safe bounded preference and strict variety. Guard rapid duplicate preview approval.
- Include non-secret preferences/learning in household export v3 and transactional restore;
  retain legacy v1/v2 imports. Browser recovery exports preserve settings drafts explicitly.

- Add optional PWA meal reminders: per-device consent/preferences and offline drafts,
  household-time/DST scheduling, durable retries/receipts and editor-safe notification links.
  Encrypt subscription/VAPID secrets; pin vendor DNS/TLS destinations. Tests cover actual
  cryptography and an injected real browser-worker event; live delivery remains unverified.

- Rename the product to mealf across the PWA, console, install metadata and download names.
  Keep existing sessions, offline stores, API headers and archive formats compatible. Original
  supplied peach/wordmark PNG installation is pending access to the attachment files.

- Edit saved weekly templates offline: rename and add/remove/change meal slots, with
  decimal-comma portions, input validation, cancellation and reload persistence. Applying
  a template uses the selected calendar week; editing it preserves existing meals.

- Bind temporary pantry shopping inclusions to a household civil week, preserving offline
  intent and legacy replay receipts. Migrate old overrides transactionally using their
  previous server acceptance time without rewriting sync history.

- Deliver the primary installable PWA at `/app/` in the existing container, with the approved
  food/glass visual direction, system light/dark appearance and English/German controls.
- Add recipe editing/drafts/photos/scaling/nutrition, calendar/recurrence/copy/templates,
  leftovers/pantry, local suggestion previews and explicit import review.
- Preserve offline work through transactional IndexedDB records/outbox/photos/drafts,
  grouped suggestion approvals, rejected-photo isolation, tombstones and archived recovery.
- Exercise real browser setup, offline reload, two-device ordering/deletion recovery,
  planning/pantry/import workflows and automated accessibility checks in CI.
- Package only public client assets in the service-worker allowlist; keep auth in isolated
  rotating HttpOnly cookies and ship browser dependency notices with a version/licence gate.

- Record the user-confirmed PWA-first delivery decision while retaining native iOS code.
- Add isolated HttpOnly browser sessions/bootstrap, transactional import history checks and
  a typed IndexedDB/outbox/sync foundation with authentication and offline safety tests.

- Inventory locked Python wheel licence declarations and installed attribution-file hashes;
  gate dependency/licence drift in CI and attach the report to future protected releases.

- Add authenticated, bounded read-only job/import diagnostics with consistent queue counts
  and explicit error-code redaction. Type and filter the existing recent-jobs endpoint.
- Show localised queue totals and recent import states in the administration overview;
  verify language switching and hidden private content with Chromium.

- Parse supported metric/English/German ingredient quantities, fractions and ranges before
  import review; preserve uncertain text and disclose omitted/truncated entries.
- Extend Docker acceptance checks through durable import preview and explicit confirmation.

- Replace Debian runtime packaging with pinned official Python/Alpine to remove unused
  util-linux packages; full Docker smoke and a zero HIGH/CRITICAL AMD64 scan pass.
- Repair the scanner action/release pins and add native AMD64/ARM64 CI test/scan jobs.

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
