# Implementation checklist and evidence

**Peach interaction, 2026-10-21 — implemented and locally tested; publication pending:**
shared PWA/console native peach buttons activate a silent hand-swipe/wobble and rotating
EN/DE reactions. Wordmark navigation is separate. Reduced motion, repeated taps, keyboard,
caption bounds and offline use pass Chromium checks. More food innuendo appears in login,
Home and selected empty states; security/help/errors stay literal. Local 226 backend and
39 frontend tests, lint/type/build/contract/brand checks and PWA/admin/push browser flows
pass. Physical Safari/iPhone is unverified; native remains unchanged. See PEACH_EGG.md.

**POC publication:** the user requested the first installable preview on GHCR. A separate
tag-triggered workflow requires all six exact-source CI jobs and fresh native-architecture
image scans/Docker checks before publishing the verified bytes. It creates a POC prerelease,
not stable acceptance. See POC.md; record actual publication/digest/pull evidence separately.

**Brand update, 2026-10-21:** both original PNGs were received in a ZIP and are preserved
byte-for-byte. The PWA/console now use the peach and image wordmark, including touch,
manifest and maskable icons. Source/derived hashes and browser/packaged-asset checks track
delivery. Storage/session/API identities and the glass UI remain intact. Retained native
artwork is not changed by this PWA release. See BRANDING.md.

**Web palette/voice update, 2026-10-21 — tested locally; publication pending:** the user-approved cream/coral/peach light and cocoa/peach dark Mealf direction now covers the PWA and administration console. Shared semantic accent tokens are exported byte-for-byte to `/app/theme.css`; the console reuses them with glass navigation, system headings, solid forms and a direct PWA link. Original PNGs and persistent/API identities are preserved. Localized food innuendo is confined to welcome/login, empty-state, sidebar and footer copy; setup/help, security, errors and recovery stay literal. Native is unchanged.

- **Tested:** 213 backend and 39 web core tests; Ruff lint/format, mypy, contract drift, frontend build/type checks, original/derived asset bytes and licence inventory. Chromium PWA, administration and push-receiver workflows passed with synthetic external-service data. Expanded admin Axe covers setup/login and all six pages in both themes; PWA palette-pair checks and 320px/200% text overflow checks passed.
- **Partial:** this records the implemented visual scope and local checks. The [manual palette finish review](validation/mealf-palette-review.md) records **ship within the reviewed palette, administration and copy scope**, with zero required material findings. Fresh exact-source CI/image scans/publication have not yet completed for this palette tree. Earlier published POC .4 evidence is historical.
- **Unverified:** physical iPhone/Safari, live Web Push/Bring!/AI, full manual accessibility and complete-product acceptance. Launcher/detector and plugin-schema validation were unavailable; no pass is claimed. See [DESIGN.md](../DESIGN.md), [BRANDING.md](BRANDING.md) and the [admin surface brief](../.impeccable/surfaces/admin.md).

**Delivery update, 2026-10-21:** the user chose PWA-first and retained native code for later.
The primary client is `frontend/`, served by this same container at `/app/`; no third
repository/service is required. See PWA.md and PWA_IMPLEMENTATION.md for current browser
coverage and limits. The original native-phase roadmap below is historical; native
signing/TestFlight is deferred rather than a PWA blocker. Latest native source 805d043
passed 90 core tests, native app/Share/Widget compilation and simulator demo/onboarding/
German light/dark flows in run 39590881768 (validation/github-native-mealf-name.json). Physical-device capabilities remain unverified.

Status vocabulary: **tested** means executed automated/local checks; **unverified** means
code exists but its relevant platform/service was not exercised; **partial** means known
requirements are missing; **planned** means no functional delivery is claimed.

No development phase or full-product acceptance set is marked complete. This is an initial
implementation across the phase boundaries; later-stage foundations do not imply earlier
phases have passed every acceptance gate.

The phase-0 dependency review now includes a reproducible 40-wheel licence/attribution
inventory and CI drift gate. Full OS/bundled-library/source-distribution review remains a
release gate; the wheel metadata baseline does not establish legal clearance. See
DEPENDENCY_LICENSES.md. Phase-1 read-only job/import diagnostics and its localised console
overview pass backend and Chromium checks on remote run 39567118930 at 17f4b9e.

| Phase | Delivered code / documentation | Status and remaining work |
| --- | --- | --- |
| 0 Architecture | ADRs, diagram, schema, sync design, initial threat analysis, OpenAPI and executable Bring probe; two local Git repos | Partial: live Bring feasibility and full dependency license inventory pending; both GitHub repositories published |
| 1 Backend | Docker, migrations, setup, sessions, offline-capable revocation, rate limits, local recovery, jobs, typed read-only job/import diagnostics, admin page navigation and household/session/AI/Bring controls, JSON/ZIP transfer, generated contract | Tested core; partial deletion/diagnostics/storage controls, quotas, remaining typed responses and broader security/load tests |
| 2 iOS foundation | SwiftUI tabs/onboarding, URL/QR sources, SQLite outbox, URLSession, Keychain, local authentication, localisations | Swift core tested on Linux; native app/extensions unverified on Apple SDK; rejected-change/archive recovery core tested, native recovery unverified; durable full resync core tested; native workflow validation remains |
| 3 Recipes | Backend typed CRUD and native editor, decimal scaling, notes/ratings, immutable photos, durable offline photo queue | Backend/core tested; native unverified; photo cleanup, fractions/ranges UX, searching API and historical metadata incomplete |
| 4 Planning | Meal CRUD, bounded recurrence, template records, leftovers validation, pantry, rated/history/leftover-aware local suggestions, replay-safe live approval, native calendar/drag/move, day/week copy, template previews, recurrence, leftover and review interfaces | Backend/core tested; native unverified; arbitrary copy destinations, cross-device approval collision UX remains partial; shared preferences/learning are tested in the PWA |
| 5 Bring | SDK adapter, encrypted credentials, list selection API, projection, UUID ownership/replay/purchase/rollover tests, durable retries | Synthetic connector tests; live unverified; browser configuration tested with doubles; additional purchased requirement semantics incomplete |
| 6 Imports/AI | Public HTTPS safety, JSON-LD drafts, conservative metric/EN/DE ingredient parsing, import review confirmation, idempotent requests, encrypted admin configuration, synthetic connection probes, request budgets, text AI provider adapters, share inbox and review UI sources | Partial: source-specific captions/transcripts, broader ingredient-language parsing, live providers, image extraction, native lifecycle validation |
| 7 UX | Dashboard/start-screen settings, system appearance, native components, localisation, 14-day widget cache/deep links and opt-in local reminder settings/reconciliation | Core dates/DST/cache/links tested; native delivery/rendering/permission/lock lifecycle, accessibility, photography and UI performance unverified |
| 8 Release | Local backup, media-aware JSON/ZIP restore, independent CI configuration, governance and release instructions | Partial: Apple build/signing/TestFlight, demo, screenshots/icons, ongoing dependency monitoring, full security review, stable releases |

## Executed evidence

Backend pytest suite, lint/type checks, generated contract drift checks, Docker build and
read-only-container health/identity/console smoke checks are executed during development.
Swift core is compiled and its offline persistence/queue tests run in a Linux Swift 6.2.1
container with SQLite. The validation report records final counts and exact limits.

The critical Bring test `test_never_deletes_or_overwrites_manual_items` asserts that a
manually created Flour item is unchanged through desired-state creation and removal.
Other tests cover duplicate replay, partial external success, owned UUID removal, purchased
suppression and new-period identity. No live Bring smoke test was executed.

## External blockers

- Both GitHub repositories are published under CLOUDCOOKCH. Initial backend tests, browser
  workflows and Docker smoke checks passed on GitHub; native compilation and security
  scanning encountered CI setup failures which were corrected. Native build validation
  continues; no stable release exists.
- The interactive workspace is Linux. GitHub supplies Xcode 26.6 and supported simulators;
  native compilation is being exercised there. Physical devices, an Apple developer team,
  signing profiles and App Store Connect credentials remain unavailable.
- No Bring test account/list or AI endpoint credentials were supplied. Tests use synthetic
  connectors and HTTP responses. Automatic Bring writes stay disabled without proof.

These blockers do not explain incomplete independent functionality: cross-device approval recovery,
admin deletion/extended diagnostics, backup replacement, safe media cleanup, non-recipe archive reconstruction, native validation and release assets
are tracked as remaining engineering work, not falsely labelled credential-blocked.


## Latest verification

The current PWA integration passes 213 backend tests and 39 web core tests locally,
Ruff lint/format, Python types, generated OpenAPI drift, strict TypeScript/format, the
Python licence baseline and full npm advisory audit (zero known advisories observed).
Real Chromium covers isolated demo, EN/DE light/dark phone/desktop, secure setup, offline
recipe save/reload, independent cookie sessions, server-ordered conflicts, deletion with
rejected-edit recovery, calendar assignment, cooked leftovers, pantry and explicit import
review/confirmation. The expanded flow covers offline template editing/reload, validation,
cancellation and next-week application. Axe checks pass on the stated Home/Recipes/Settings/
Calendar screens and the phone template editor;
full manual accessibility and real iPhone/Safari are separate gates.

An independent visual/source review and one bounded fix pass scored dialog naming and
singular/localised serving copy resolved. Its scope is the captured screens and listed
fixes, not complete product acceptance. The design launcher/detector were unavailable;
manual review does not pretend they passed. Genuine screenshots and asset provenance are
recorded in the PWA validation material. Current Docker smoke/security CI is recorded
separately for the exact image/commit; do not apply earlier green runs to a newer tree.

The overall project remains partial. Live Web Push validation, complete archive reconstruction, broader source/media import,
admin deletion/destructive replacement, safe media/sync compaction and release validation remain engineering
work. Live Bring!/AI accounts and physical browser devices are external validation gaps.
No stable release or protected release acceptance is enabled by these development results.

Published PWA ff48270 and pantry-period correction 0e0c692 each passed all six GitHub CI
jobs, including native AMD64/ARM64 test/Docker/security jobs and Chromium. Exact source and
job IDs are in validation/github-pwa.json and validation/github-pantry-period.json. The
template editor at 48c23e4 also passed all six jobs in run 39587189774. See
validation/github-template-editor.json for the exact image IDs, scanner, architecture/job
evidence and limits. Documentation-only follow-ups do not change that application source.

Opt-in PWA reminders now have per-device controls/offline drafts, durable household-time
scheduling and privacy-preserving payloads. Unit/API encryption/retry/security and real
Chromium receiver/navigation tests use explicit subscription/vendor doubles. No live vendor,
physical iPhone or OS delivery is claimed. See REMINDERS.md and ADR 011.

Reminder implementation source 8c946b6 passed all six GitHub jobs in run 39596349930:
180 backend tests per AMD64/ARM64 runner, 34 web tests, full ordinary/reminder/console
browser flows, Docker restart/restore and unsuppressed HIGH/CRITICAL security gates.
See validation/github-reminders.json for exact images, jobs, artifacts and synthetic/live
limits. This verifies the development implementation, not live vendor/device delivery.

Shared planning defaults and bounded approval learning are implemented with typed authenticated
settings, server-ordered/replay-safe saves, cached offline scoring/drafts and atomic approval
learning. Household export v3 includes preferences/counts and retains legacy imports. Exact
source/tests/browser/CI evidence is tracked separately; see PLANNING_PREFERENCES.md.

Shared-planning source 2e7b920 passed all six GitHub jobs in run 39600337201, including
187 backend tests per AMD64/ARM64 runner, 39 web tests, actual two-device/offline/approval
browser flows, settings/learning Docker restart/JSON+ZIP restore and unsuppressed security
gates. Exact source/images/jobs/artifacts and limits: validation/github-planning-preferences.json.

Conservative retention now has bounded hourly terminal import/diagnostic/session cleanup,
startup-only stale transfer cleanup and local CLI dry-run/apply. Import fingerprints preserve
request replay after raw-source pruning; late workers preserve terminal confirmation.
Offline sync/Bring receipts and media stay retained. See RETENTION.md for scope/evidence and
remaining full deletion/compaction work.

Retention source 9fffb7b passed all six GitHub jobs in run 39604741072: 200 backend
tests per AMD64/ARM64 runner, unchanged 39 web tests, full browser/packaged CLI/Docker
restart/restore checks and unsuppressed security gates. Exact images/jobs/artifacts and
limits are in validation/github-retention.json.

The first user-authorised POC is published as `poc-20261021.1` from 4deb195.
All six exact-source CI jobs passed in run 39607765691 (209 backend tests per architecture,
39 web tests). Preview publication run 39608095928 separately passed fresh native AMD64/ARM64
image scans and Docker persistence/restore checks, then published those verified bytes to
`ghcr.io/cloudcookch/mealf-server`. The multi-architecture digest is
`sha256:b4da38f72b1c7c1548f3058a39319d23b7001ad6a7b74651dccd2fece7a20ecb`.
Anonymous pull/manifest inspection and a fresh E2E against the pulled AMD64 image passed.
Public release assets were downloaded and their checksums verified; scan report identities
match the published image configurations. See validation/github-poc-preview.json and POC.md.
This is a prerelease; it does not enable stable acceptance or imply live-service/iPhone testing.

Bash-enabled POC `poc-20261021.2` from 366e391 passed all six source CI jobs in run
39610992728 and all preview publication jobs in run 39611318654. Both architectures
exercise `/bin/bash`, a real pseudo-terminal, private setup-token reading and packaged GPL
notice as the normal non-root account. Fresh release scans retain the unsuppressed gate.
Anonymous pull and a local .1-to-.2 upgrade on a disposable shared volume passed: the token
was preserved, the new image served internal port 5152 with a healthy overridden check,
and setup using that original token succeeded. The user's actual NAS UI/token were not
accessed. Exact digest/images/jobs/assets and limits: validation/github-bash-preview.json.

User-requested setup-token logging is published in `poc-20261021.3` from 1282fa4.
Source CI 39612946770 passed all six jobs (213 backend tests per architecture, 39 web tests).
Preview publication 39613320058 passed fresh native image scans/Docker checks, including
bootstrap using the token read from Docker logs and no added token record on configured
restart. Anonymous-pulled AMD64 .2-to-.3 upgrade on a disposable shared volume with internal
port 5152 passed: existing token logged once, same token logged after unconfigured restart,
successful setup from that log value, then configured restart with no added token record.
Passwords/session credentials remained absent; LOG_SETUP_TOKEN=false suppressed the event
while retaining file access. Historical logs remain, with the token invalid after setup.
Exact digest/images/jobs/artifacts and limits: validation/github-setup-token-log-preview.json.

Original-artwork delivery is published as `poc-20261021.4` from 9d73633. Exact-source CI
39619768791 passed all six jobs, including 213 backend tests per architecture, 39 web tests,
source/derived brand checks, offline image delivery and actual packaged output hashes.
Publication 39620210006 repeated native image scans/Docker checks before publishing verified
bytes. Anonymous pull and a .3-to-.4 same-volume upgrade on internal 5152 passed: household,
session, existing recipe and sync proof are preserved, and served artwork matches the
original-source/derived provenance. No scanner allowlist was weakened. Earlier failed
test-helper/evidence-field attempts and exact final images/jobs/assets are recorded in
validation/github-mealf-artwork.json. Physical iPhone icon refresh and native artwork remain
outside this PWA/console acceptance. Historical screenshot/review records retain their scope.

PWA touch refinement, 2026-10-21: implemented and tested in Chromium. Pinch/double-tap keep
visual viewport scale at 1, finger swipes scroll and reading text remains selectable. Safari
cancelable gesture handlers and Ctrl+wheel versus normal wheel are covered; keyboard/OS
accessibility zoom and normal viewport metadata are retained. Full PWA browser flow,
213 backend/39 web tests, lint/format/type/build and OpenAPI checks pass. No visual tokens,
admin behavior, storage or API contracts change. Physical iPhone/Safari is unverified;
container publication remains blocked pending a successful Actions run on current source.

Preview retry correction: the operator's log is attempt 2 of old publication 39620210006
at tagged source 9d73633, not a publication of current main. It pushed a rebuilt `.4` image
then failed creating its existing release. New workflow preflight preserves completed
previews without builds/writes and refuses reused partial image tags. Added 12 unit cases
for completed/mismatched releases and API failures; original exact-source/security gates
remain intact. The palette-only validation commit 5c74bbc now has successful CI 39624790084;
it cannot validate later gesture/retry commits. Fresh combined-source verification and `.5`
publication are pending. The existing `.4` Git tag and release assets are not moved/replaced.

Confirmed selection refinement: app controls and labels are non-selectable; recipe detail
text/source attribution and inputs remain selectable. The browser test selects an actual
recipe word and input range rather than the padded empty area of a step row. No gesture,
scrolling, input-editing or admin behavior is removed. Added workflow_dispatch to full CI;
the source gate accepts that event only with the same exact SHA/main/repository/workflow
checks and all six successful jobs. This provides a concrete manual trigger when a push
has no Actions run; old `.4` reruns still cannot publish newer main source.

Current publication: `.5` is verified and published from d15b37a. All six CI jobs in
39628446235 pass with 226 backend tests per architecture and 39 frontend tests. Both fresh
native release images in 39629099312 attempt 1 pass unsuppressed HIGH/CRITICAL gates and
Docker checks. Anonymous pull and same-volume original-digest `.4` to `.5` upgrade preserve
household/session/recipe/sync history on internal 5152. The actual completed-release retry
(attempt 2) succeeds without image builds or registry/release writes; digest and release
body/assets stay unchanged. The previous pending/blocked observations above are historical
and superseded by validation/github-preview-retry.json. Native/physical-iPhone/live-service
and complete-product acceptance remain open. Keep existing volumes/ports and reload/accept
the PWA update after finishing edits; clearing browser data is not required.
