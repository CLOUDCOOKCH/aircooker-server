# Validation evidence — 2026-10-21

This report describes a development implementation, not completed product acceptance.
No real household, Bring account, cloud AI credential or Apple signing credential was used.

Latest diagnostics change: **136 pytest tests pass**, including seven authentication,
bounded-query, queue-count/filter and secret/content redaction checks. Ruff lint/format,
mypy across 25 modules and generated OpenAPI drift checks pass. This adds read-only typed
job/import projections, with no migration, worker scheduling or connector mutation changes.
Current Docker and remote CI checks are pending. The evidence below also retains earlier
development runs and does not imply all listed platforms validated this newest change.

GitHub run 39565110991 at e10d40d subsequently passes all five jobs: 136 tests and real
Docker smoke on AMD64/ARM64, both dependency/secret/container security gates and Chromium
administration workflows. Exact job IDs are in validation/github-diagnostics.json.
The later console overview now displays bounded import/job rows and queue totals; its
expanded local Chromium test passes EN/DE switching and proves private markers/URLs do
not appear in the document. Genuine desktop/light/dark and German phone captures were
regenerated and visually inspected. Later console changes await their own remote CI.

Console run 39567118930 at 17f4b9e passes all five remote jobs, including the new browser
diagnostics/language/redaction checks. The wheel-licence inventory now runs locally against
all 34 locked runtime packages with installed attribution files; a deliberately changed
approval baseline is rejected. Ruff checks pass. This is metadata/attribution evidence,
not full container/native-library or legal clearance; see DEPENDENCY_LICENSES.md.

| Check | Executed result | Limit |
| --- | --- | --- |
| Backend tests against hashed runtime dependencies | **129 passed** | One upstream Starlette TestClient/httpx deprecation warning; no failure |
| Ruff lint and format | Passed | Python source/tests/scripts only |
| mypy | Passed across 23 application modules | `check_untyped_defs`, not exhaustive strict typing |
| OpenAPI regeneration/drift | Passed | Version 0.1.0, API-major/sync-protocol 1/1 |
| iOS vendored contract checksum / fields / paths | Passed | Does not replace Apple SDK or semantic integration tests |
| Swift core compile and tests | **80 passed**, Swift 6.2.1 Linux | No SwiftUI/UIKit/WidgetKit/Keychain/Face ID runtime validation |
| Swift source formatting and native syntax parse | Passed | Syntax parsing is not Apple framework type checking |
| Localisation parity | 283 EN/DE keys and static localised error lookups passed | Human translation/a11y audit outstanding |
| Docker build | Passed, linux/amd64 | ARM64 publication/runtime not executed |
| Docker E2E | Passed | Real HTTP + SQLite; synthetic household, no Bring service |
| Chromium administration console | Passed | Loopback development origin; production TLS ingress not validated |
| Source Gitleaks 8.28.0 scans | No findings in both repositories | Build outputs/installed tooling excluded, source tests included |
| pip-audit 2.9.0 on runtime lock | 34 packages, no known advisories reported | Advisory database coverage is finite |
| pip-audit on optional browser/development lock | 45 packages, no known advisories reported | pytest upgraded to 9.0.3 after an advisory was detected |
| Trivy 0.70.0, Alpine candidate | **0 HIGH / 0 CRITICAL**, no unfixed exclusions | linux/amd64 image; advisory coverage is finite; ARM64 pending |
| GitHub workflows | Backend tests, browser workflow, Docker smoke and Swift core checks passed | Native build found/fixed missing assets and a section initializer; further Apple checks pending |

Docker E2E verifies non-root/read-only startup, token-protected setup, HTTP authentication,
idempotent mutation replay, recipe/meal persistence and scaling projection, server restart,
replayed offline edit, immutable photo upload/replay, exact photo bytes after restart,
leftover ingredient exclusion, suggestion approval/replay across server restart,
encrypted AI configuration/redaction across restart, JSON v2 and streamed ZIP restore into independently configured clean containers. The latest
image also passes stable commit-proof persistence, protected delta/push requests and snapshot
pagination across restart and later recipe edits. It does not substitute for a physical two-device iOS workflow.

Real Chromium checks exercised first-run setup/login, household settings, unsaved-input
preservation during EN/DE switching, mobile layout, encrypted AI settings/probe, Bring
list selection/retry, JSON import, ZIP download, duplicate archive rejection, device-session
revocation, password change and absence of JavaScript errors. AI/Bring adapters were explicit
test-only doubles; these checks do not establish live-service compatibility. Screenshots are genuine Chromium output with
a synthetic household: [desktop](screenshots/admin-desktop.png),
[German mobile](screenshots/admin-mobile-de.png). No fabricated iOS screenshots exist.

## Container security result

The current runtime switches to the pinned official Python/Alpine base described in
[ADR 009](adr/009-container-runtime.md). Candidate image
`sha256:9ccbfe4c48216c0281477561a1f43ac61a95bbf70d213069b51bd3eb3065a896`
is 135,073,697 bytes and passes the full Docker smoke script. Trivy 0.70.0 reports zero
HIGH/CRITICAL findings using a freshly fetched database, without suppressions or unfixed
exclusions. See [current scan](validation/container-security-alpine.json). The scanner
recognises Alpine 3.24 and uses its vulnerability repository, but warns that its static EOL
table does not list that OS version. This scan is not proof that all vulnerabilities are
absent. AMD64/ARM64 CI checks and scans now run natively; ARM64 evidence is still pending.

The committed scan omits unrelated ImageConfig environment/build history. Those fields
contained the official base image's public GPG verification key, which triggered two
generic-key detections. Image identity, layers, OS, package inventory and vulnerability
results are retained; no secret-scanner allowlist or vulnerability suppression was added.
CI archives the complete scanner report separately.

Historical Debian findings follow; they are retained without claiming remediation within
that old image.

The initial Python 3.12.12/Debian 12 image had 9 critical and 91 high package/advisory
matches. It was replaced with the verified multi-architecture Python 3.12.14/Debian 13 image
pinned by digest. Published PCRE2/OpenSSL package fixes were installed at exact versions.
The resulting candidate has no critical matches and no remaining matches with published
fixes in the scanner's data, but still fails the configured HIGH/CRITICAL gate.

See [machine-readable container findings](validation/container-security.json) and
[runtime dependency audit](validation/dependency-audit.json) and
[browser/development audit](validation/browser-dependency-audit.json). Forty-four matches represent eight
unique advisory IDs repeated across binary packages, not 44 independently validated
application vulnerabilities. They must be triaged against actual runtime paths and tracked
until remediated or explicitly resolved with evidence. No scanner suppression was added.
The first Trivy mirror was unavailable; the supported GHCR database repository succeeded.

## Not verified / incomplete

Successful native SDK build, supported iOS simulator/device UI tests, share/widget lifecycle,
notifications, native photo-picker/cache UI, accessibility, macOS signing and TestFlight upload remain
unverified or incomplete. No live Bring compatibility report was generated. No live AI
provider was contacted. Social source-specific captions/transcripts are incomplete.
Both independent GitHub repositories and CI runs are now published. No stable release,
TestFlight build or physical-device acceptance result exists.

Media tests additionally cover metadata stripping, file/pixel/quota limits, immutable
identity, archive traversal/corruption, duplicate rollback, historical deletion/provenance
restore, CSRF and chunked upload bounds. Swift tests cover photo/outbox restart and failed
transaction rollback, lost response replay, local schema upgrades, bounded recurrence,
exceptions, civil-date arithmetic, detached moves, template recipe references and atomic
copy batches. Native photo/calendar UI sources were formatted and syntax parsed only.

New tests cover leftover edits/deletion/discard with existing bookings, simultaneous
reservations from two authenticated devices, deterministic history/rating/variety scoring,
reservation-aware suggestions, transactional approval rollback/replay/staleness and occupied
slot preservation. Python and Swift execute the same pinned three-case fixture. Native
source parsing and core tests do not establish Apple UI lifecycle or accessibility. Portable
reminder/widget tests additionally cover household dates, DST gaps/repeated hours, grouped
chronological limits, strict deep links, 14-day cached rollover/expiry, privacy and malformed
cache bounds. UserNotifications/WidgetKit delivery/rendering and local logout cleanup remain
Apple SDK/device validation work.

See IMPLEMENTATION.md for remaining work: shared recommendation preferences, cross-device
approval recovery, admin deletion/extended diagnostics, destructive restore, cleanup, non-recipe archive reconstruction and native validation. External credential gaps do not excuse these missing features.

The companion Swift recovery suite now verifies rejected-record isolation, persistent server
snapshots, transactional multi-edit archives and new recipe identities, later archive
restoration, stale-review protection, active-sync exclusion, malformed receipts/deltas, and
local schema-v3 migration replay. Native review/sharing controls remain Apple SDK unverified.

History recovery checks also exercise real SQLite online backup/rollback, reused sequence
values with different commit proofs, rejected stale-proof pushes/pulls, migration backfill,
anchored pages during later writes, soft payload budgeting and a shared Python/Swift wire
fixture. Companion tests cover durable restart/resume, another restore mid-download,
acknowledged-before-pull proofs, staged/final rollback, malformed payloads, missing-proof
upgrade and recipe photo/import-attribution restoration. Apple lifecycle checks remain open.

See [history verification record](validation/sync-history.json) for the executed image and
counts. The last Python dependency audit artifacts are from 2026-10-20; their locks have not
changed in this increment. Chromium admin workflows were also exercised previously; no
browser administration UI was changed or revalidated in this increment. An initial final
build/test launch ran out of Docker storage; obsolete mealf images/build cache were
removed without deleting volumes, then affected image and Swift checks passed.

The final 66-test Swift run used the compiler extracted from the same pinned Swift 6.2.1
OCI image after VFS container allocation exhausted local Docker storage. Manifest and layer
SHA-256 digests were verified; Debian SQLite headers were checked against package metadata.
An earlier 65-test run passed inside Docker. Final lint/native syntax checks passed; Apple
framework type checking remains unavailable. Only reconstructible compiler images/build
cache were retired; no household volume was removed.

Latest source map: `migrations/005_sync_history.sql`, `sync_history.py`, `sync.py`, `models.py`
and `app.py`; OpenAPI and `sync-history-v1.json`; `test_sync_history.py` and extended Docker
smoke; API/backup/schema/ADR/checklist documentation. Companion code and controls are listed
in its independent validation report.


## Device sign-out increment

See [session sign-out evidence](validation/session-signout.json) for the current image and
counts. The final suite has 97 backend and 76 portable Swift tests; Ruff/type/OpenAPI checks
and source secret scans pass. The updated Docker E2E revokes a rotated refresh capability
without an access token, retries it, restarts the container and confirms that the revoked
device stays rejected while the original device still works. The full photo/sync/restore
smoke remains passing. No browser admin UI was changed or rerun in this increment.

New source map: `auth.py`, `app.py`, `recommendations.py`, `test_session_revocation.py`,
`test_recommendations.py`, `scripts/docker_smoke.py`, generated OpenAPI, ADR 008,
API/security/planning/checklist/changelog documentation and validation artifacts. No schema
migration, dependency lock or deployment setting changed. The refreshed Trivy report still
has 44 HIGH matches across 8 advisory IDs and no CRITICAL or published fixes; its gate fails.
Native UI/Keychain lifecycle, physical devices and live external integrations remain open.

A full test run initially exposed an existing seed-sensitive recommendation failure. Both
languages now sort by use count before rating/history score; new extreme-rating/history
regressions exercise ten seeds. All three existing cross-language fixtures remain unchanged
and pass. Earlier history-specific counts above are historical evidence, not the current total.


## Interface refinement

Chromium workflows pass after replacing the long accordion with six persistent settings
pages and desktop/phone navigation. Tests verify existing setup, cookie/CSRF, account,
AI/Bring configuration, JSON/ZIP transfer and password workflows; section/language changes
preserve unsaved fields. All six pages remain within a 320px viewport at 200% root text
size. This is a text-size check, not an assistive-technology audit. Light/dark desktop,
German phone overview/settings/AI and initial setup were captured from the running
synthetic household and visually inspected. See ADMINISTRATION.md for exact image paths.

Body/muted/navigation color-pair calculations exceed 4.5:1; control boundaries exceed 3:1
against their panel backgrounds in both palettes. This is a bounded token check, not a
claim that every state passed a complete accessibility audit. No external fonts, tracking
or invented recipe images were added. No HTTP security policy was relaxed.

97 backend tests and 76 companion core tests still pass; lint/types/OpenAPI/contract and
262-key localisation checks pass. Native Home/recipe/calendar sources were refined but
remain unverified against an Apple SDK. No release gate is cleared by UI changes.
The exact server source changes are `web/index.html`, `web/console.css`, `web/console.js`,
`scripts/browser_smoke.py`, documentation and six genuine browser captures. Runtime
schemas, migrations, dependency locks and the canonical API contract are unchanged.


## Published foundation and deterministic ingredient import

GitHub [run 39558393279](https://github.com/CLOUDCOOKCH/aircooker-server/actions/runs/39558393279)
passed all five jobs at e55e008: native AMD64/ARM64 tests, real-HTTP Docker smoke and security
gates, plus Chromium workflows. See [job identities](validation/github-foundation.json).
Security no longer depends on suppressing the historical Debian matches.

The subsequent ingredient parser adds 32 tests for metric units, ordinary/mixed/Unicode
fractions, ranges, decimal commas, preserved ambiguity, non-numeric scaling, malformed source
entries and truncation warnings. Full backend total: 129 passing tests, with Ruff, mypy
(24 modules) and unchanged OpenAPI checks passing. A reviewed import is additionally tested
through servings scaling, compatible-unit aggregation and pantry exclusion.

Docker image sha256:2682f75dfbd094eec3563d61bdec8c302ac2729b722a73933d5cc5be1316e59d
passes the expanded smoke script: its durable worker produces a fractional-ingredient
preview, the library remains unchanged before explicit confirmation, and the confirmed
recipe participates in JSON/ZIP export and clean-install restore. No live source account
or AI provider was used. The API schema/pin is unchanged. Native translated review notices
are implemented sources; their editor lifecycle remains unverified until Apple UI tests.

## PWA opt-in reminder implementation, 2026-10-21

The current development suite passes 180 backend tests and 34 web tests. Reminder checks
cover actual encryption/VAPID signatures, endpoint/DNS restrictions, device/session/CSRF/rate
controls, encrypted secrets/export exclusion, DST, durable retries/receipts and obsolete-meal
suppression. The actual PWA/API/IDB controls and worker receiver pass Chromium using explicit
subscription/vendor doubles, injected push events and test-controlled permissions. The full
ordinary PWA smoke still passes. Exact local evidence/captures and fresh bounded manual UI
review are in validation/reminders-local.json and validation/reminders-review.md. No live
vendor/device delivery, user permission dialog or physical Safari acceptance is claimed.
Current CI must be read for its exact source; prior mealf-name green runs cover name-only
source (validation/github-mealf-name.json and github-native-mealf-name.json).

Reminder implementation source 8c946b6 passed all six GitHub jobs in run 39596349930:
180 backend tests per AMD64/ARM64 runner, 34 web tests, full ordinary/reminder/console
browser flows, Docker restart/restore and unsuppressed HIGH/CRITICAL security gates.
See validation/github-reminders.json for exact images, jobs, artifacts and synthetic/live
limits. This verifies the development implementation, not live vendor/device delivery.

## Shared planning defaults and explicit-approval learning, 2026-10-21

187 backend and 39 web tests pass locally, including server-ordered/replay-safe preference
saves, once-only atomic learning, strict variety, leftover choice, snapshot/draft validation
and export/restore rollback. Actual Chromium covers two independent cookie sessions, saved
household choices, offline draft/reload and 21-meal local approval/learning. Two same-turn
activations create exactly one 21-mutation IndexedDB approval group. Stated settings/preview
Axe checks, notification/console regressions and Docker restart/JSON+ZIP preference/learning
restore pass. The manual UI reviewer scored its duplicate-approval/recovery-copy findings
resolved at this scope. Exact local evidence/capture hashes: validation/planning-preferences-local.json;
review: validation/planning-preferences-review.md. CI for this source is recorded separately;
prior reminder green evidence does not certify this newer tree. No full product, original
artwork, physical browser or live external-service acceptance is claimed.

Shared-planning source 2e7b920 passed all six GitHub jobs in run 39600337201, including
187 backend tests per AMD64/ARM64 runner, 39 web tests, actual two-device/offline/approval
browser flows, settings/learning Docker restart/JSON+ZIP restore and unsuppressed security
gates. Exact source/images/jobs/artifacts and limits: validation/github-planning-preferences.json.

## Conservative retention and terminal import safety, 2026-10-21

The complete backend suite passes 200 tests; thirteen focused cases cover bounded/dry-run
cleanup, old import replay/editing/proof preservation, pending/unknown legacy sources, session
references, notification/Bring receipts, startup file safety, multi-batch migration/rollback,
late confirmed-worker races and redacted maintenance failure with worker continuation.
Expanded ordinary PWA and console browser regressions plus non-root/read-only Docker CLI,
restart and JSON/ZIP restore pass. Types/lint/format/OpenAPI drift and the unchanged 40-package
licence baseline pass. Frontend source/visual design is unchanged; no new visual or physical
platform acceptance is inferred. Exact local image/count/scope: validation/retention-local.json.
Current CI is recorded separately; prior shared-planning green evidence does not certify a
newer maintenance tree. See RETENTION.md for logical pruning and deliberately retained data.

Retention source 9fffb7b passed all six GitHub jobs in run 39604741072: 200 backend
tests per AMD64/ARM64 runner, unchanged 39 web tests, full browser/packaged CLI/Docker
restart/restore checks and unsuppressed security gates. Exact images/jobs/artifacts and
limits are in validation/github-retention.json.

## Mealf identifiers and administration paths — 2026-10-22

Published and verified in `poc-20261022.5`. Current source/package/native target names
use Mealf. Console `/admin/` and its assets no longer occupy `/`; the root is reserved
for the operator's landing page. PWA/API paths remain stable. Existing databases,
sessions, archives and browser offline state have explicit compatibility handling.
See [upgrade and path routing](MEALF_MIGRATION.md).

Exact-source main CI passes: 392 backend tests on each architecture, 59 frontend core
tests, Ruff/mypy/format, OpenAPI drift, original assets, licence/dependency/secret checks,
and Chromium/WebKit workflows. Both fresh native image scan/runtime/operator gates pass;
public hashes, manifests/configs, attestation and anonymous pull are verified. The
published .4-to-.5 same-volume 5152 upgrade preserves identity/session/history, offline
replay, recipe/photo and synthetic purchased Bring ownership; real EN/DE OCR previews
and old ZIP/photo restore into a clean new image pass. A real Chromium old/new-PWA
upgrade additionally preserves exact offline outbox/mutation/device/image IDs and Blob
hash, reuses the existing browser database, rotates legacy cookies and opens `/admin/`.
Root/old-console assets return 404. No assertion/gate was suppressed on CI retries.
See [the exact source and release evidence](validation/github-mealf-rename-preview.json).

The fresh finish review records **ship within name, routing and visual-preservation
scope** in [the review](validation/mealf-admin-routing-review.md); the documentation
handoff preserves incumbent tokens. Launcher/detector remain unavailable. The local
source image build was restricted by Alpine HTTP 403; published images for both architectures
were built/scanned/run in GitHub and pulled/exercised locally. Initial extra local
upgrade harness/disk failures and successful reruns are recorded in the evidence.
Physical iPhone and live external integrations remain unverified; full v1 acceptance
is open. Actual GitHub repository names still require owner renaming in Settings.
