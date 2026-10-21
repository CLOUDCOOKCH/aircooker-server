# Changelog

- Add native camera/image choosing for recipe screenshots and photos of written recipes.
  Local EN/DE OCR produces a durable editable preview; saving requires explicit review.
  Persist source images and queued imports atomically offline, strip image metadata,
  expose correctable recognized text and retain replay/cancellation semantics. Optional
  configured AI receives only recognized text after consent. Cover real OCR, preview/save,
  offline reload, lost replies, terminal-history queue starvation and synthetic AI privacy.
  Settings avoids native push subscription discovery before notification permission;
  synthetic opt-in boundary and existing reminder flows pass. Headless WebKit image tests
  explicitly model OS push as unavailable; the photo pipeline stays real.
  Physical camera/iPhone and live AI/push remain unverified; publication evidence is separate.

- Add a shared PWA/admin theme library: Flo (existing system appearance), After Dark
  (fixed dark, ink/oxblood/rose) and Sunday (fixed light, linen/sage). Persist browser-local
  choice, apply before React starts, match native controls and browser chrome, and keep
  cross-tab administration and offline reloads in sync. Preserve original brand assets
  and household/storage/API identities. EN/DE native-radio controls include previews.
  Browser contrast/Axe, storage-failure, offline and OS-override checks are included.
  Published `.9`: all six source CI jobs (including Chromium/WebKit), both fresh image
  gates, public pull/checksums/config identities and .8-to-.9 same-volume 5152 upgrade
  pass. Narrow German navigation/demo bounds and destructive contrast are corrected;
  physical iPhone remains unverified.

- Add per-device Day/3 days/Week calendar views and touch/pointer meal drag grips with
  target feedback, edge scrolling, cancellation and tap/keyboard move forms. Preserve
  offline durability, existing desktop drops and occurrence exceptions. Stack narrow
  dialog fields and constrain native date controls to prevent the reported overlap.
  Published `poc-20261021.8`: all six source CI jobs, Chromium/WebKit interaction checks,
  both fresh image gates and public pull/checksum/5152 same-volume upgrade checks pass.
  WebKit tap/cancellation compatibility-click findings are fixed; physical iOS unverified.

- Fix phone PWA enlargement/clipping risks: minimum 16px mobile form fields, explicit
  Safari text autosizing, all-edge safe-area layout, short touch-landscape navigation and
  safe dialog bounds. Preserve accessibility zoom, selection, scrolling and stored work.
  Add real-engine layout/focus regressions with simulated notch geometry; physical iOS
  Home Screen and software-keyboard behavior remains unverified. Published `poc-20261021.7`
  after all six source CI jobs (including Chromium/WebKit), both image gates and public
  pull/checksum/5152 same-volume upgrade verification. See the exact release evidence.

- Add a silent peach-slap Easter egg in the PWA and admin console: native touch/keyboard
  activation, a hand-swipe and 560ms wobble, localized rotating comebacks and reduced-motion
  feedback. Add more English/German food jokes without changing security/help language.
  Original artwork and persistent identities remain intact. Local 226 backend/39 frontend
  tests and Chromium interaction/offline/admin regressions pass; physical Safari unverified.
  Published `poc-20261021.6`: all six source CI jobs and both fresh image gates pass; public
  pull and same-volume 5152 upgrade pass. See [interaction evidence](docs/PEACH_EGG.md) and
  [exact release evidence](docs/validation/github-peach-preview.json).

- Publish `poc-20261021.5` with the shared Mealf palette/admin design, confirmed PWA control
  selection policy and safe release retries. All six exact-source CI jobs pass (226 backend
  tests per architecture, 39 frontend tests); both fresh release images pass security/runtime
  gates. Anonymous pull, same-volume internal-5152 upgrade and a real completed-release retry
  pass. The retry changes no image digest or release body/assets. See the release evidence.

- Make completed preview-release retries a read-only no-op before image builds/pushes;
  fail closed for API errors, unexpected release records or already-used partial image tags.
  Add a manual main-branch CI trigger running the same full matrix. Preserve exact-source CI and fresh dual-architecture security/runtime gates for new versions.

- Block ordinary PWA page pinch/double-tap and trackpad-pinch zoom while keeping recipes and inputs selectable and suppressing
  accidental selection on app controls/labels. Preserve scrolling, input editing and browser/OS keyboard accessibility
  zoom. Real Chromium gesture/selection and existing PWA flows pass; physical iPhone/Safari
  is unverified. This is included in the published `.5` preview.

- Apply the approved Mealf cream/coral/peach and cocoa/peach palette throughout the PWA
  and administration console, with shared exact theme tokens, glass navigation, system
  headings, solid forms and a direct planner link. Preserve original artwork and compatible
  storage/session/API identities; native stays deferred. Add localized food innuendo to
  welcome/login, empty-state, sidebar and footer while retaining literal security/help/errors.
  Local 213 backend/39 web tests, lint/type/contract/build/asset/licence checks and Chromium
  flows pass, including expanded admin Axe and narrow/enlarged-text checks. Manual palette
  review: ship within reviewed scope, zero material findings. Publication pending; physical
  iPhone/live-service/full-product acceptance unverified.

- Install the original supplied mealf peach/wordmark across PWA welcome/loading/navigation,
  footer and console. Add versioned touch/favicon/manifest/maskable assets, retain original
  bytes and compatibility IDs, and verify original/derived/offline/packaged asset integrity.

- Show the one-time setup token in an unconfigured startup log entry, as requested by the
  operator. Preserve it across restarts/upgrades, stop emitting it after setup, and support
  `LOG_SETUP_TOKEN=false`. Keep passwords/session/integration secrets out of these logs.

- Add Bash 5.3.9 for NAS/container terminal clients requiring `/bin/bash`; exercise reading
  the private setup token through Bash as the existing non-root user on both architectures.

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
