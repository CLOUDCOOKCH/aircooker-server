# Implementation checklist and evidence

Status vocabulary: **tested** means executed automated/local checks; **unverified** means
code exists but its relevant platform/service was not exercised; **partial** means known
requirements are missing; **planned** means no functional delivery is claimed.

No development phase or full-product acceptance set is marked complete. This is an initial
implementation across the phase boundaries; later-stage foundations do not imply earlier
phases have passed every acceptance gate.

The phase-0 dependency review now includes a reproducible 34-wheel licence/attribution
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
| 4 Planning | Meal CRUD, bounded recurrence, template records, leftovers validation, pantry, rated/history/leftover-aware local suggestions, replay-safe live approval, native calendar/drag/move, day/week copy, template previews, recurrence, leftover and review interfaces | Backend/core tested; native unverified; arbitrary copy destinations, shared household preferences, acceptance learning and cross-device approval collision UX remain partial |
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

These blockers do not explain incomplete independent functionality: shared recommendation preferences, cross-device approval recovery,
admin deletion/extended diagnostics, backup replacement, safe media cleanup, non-recipe archive reconstruction, native validation and release assets
are tracked as remaining engineering work, not falsely labelled credential-blocked.


## Latest verification

136 backend tests and 85 Swift core tests pass; diagnostics redaction/count/filter tests pass. Native app/Share/Widget compilation and foundation simulator onboarding have passed on GitHub; the new offline demo UI run remains in progress. Docker photo upload, leftover exclusion, suggestion approval/replay across restart and JSON/ZIP restore pass. Chromium setup, household/AI/Bring forms, device revocation/password change and JSON/ZIP transfer passed with explicit external-service doubles. Encrypted AI settings persist across Docker restart. Runtime and browser/development dependency audits and source secret scans pass. The new Alpine runtime passed real-HTTP Docker smoke checks and Trivy 0.70.0 reports
zero HIGH/CRITICAL findings without ignoring unfixed issues. Native AMD64/ARM64 tests, Docker smoke checks, secret scans and vulnerability scans
passed on GitHub run 39559444646 for parser commit 9b4fe3c (129 tests per architecture); current diagnostics changes await their own run. The previous Debian image retained
44 high matches across eight advisories and is preserved as historical evidence.
See VALIDATION.md and its recorded artifacts. Distribution workflows require the protected
environment variable `RELEASE_ACCEPTANCE_VERIFIED=true` and are not enabled by these results.
