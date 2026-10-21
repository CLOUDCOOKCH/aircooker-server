# Implementation checklist and evidence

Status vocabulary: **tested** means executed automated/local checks; **unverified** means
code exists but its relevant platform/service was not exercised; **partial** means known
requirements are missing; **planned** means no functional delivery is claimed.

No development phase or full-product acceptance set is marked complete. This is an initial
implementation across the phase boundaries; later-stage foundations do not imply earlier
phases have passed every acceptance gate.

| Phase | Delivered code / documentation | Status and remaining work |
| --- | --- | --- |
| 0 Architecture | ADRs, diagram, schema, sync design, initial threat analysis, OpenAPI and executable Bring probe; two local Git repos | Partial: live Bring feasibility, full dependency license inventory and remote repo publication pending |
| 1 Backend | Docker, migrations, setup, sessions, offline-capable revocation, rate limits, local recovery, jobs, admin household/session/AI/Bring controls, JSON/ZIP transfer, generated contract | Tested core; partial deletion/diagnostics/storage controls, quotas, remaining typed responses and broader security/load tests |
| 2 iOS foundation | SwiftUI tabs/onboarding, URL/QR sources, SQLite outbox, URLSession, Keychain, local authentication, localisations | Swift core tested on Linux; native app/extensions unverified on Apple SDK; rejected-change/archive recovery core tested, native recovery unverified; durable full resync core tested; native workflow validation remains |
| 3 Recipes | Backend typed CRUD and native editor, decimal scaling, notes/ratings, immutable photos, durable offline photo queue | Backend/core tested; native unverified; photo cleanup, fractions/ranges UX, searching API and historical metadata incomplete |
| 4 Planning | Meal CRUD, bounded recurrence, template records, leftovers validation, pantry, rated/history/leftover-aware local suggestions, replay-safe live approval, native calendar/drag/move, day/week copy, template previews, recurrence, leftover and review interfaces | Backend/core tested; native unverified; arbitrary copy destinations, shared household preferences, acceptance learning and cross-device approval collision UX remain partial |
| 5 Bring | SDK adapter, encrypted credentials, list selection API, projection, UUID ownership/replay/purchase/rollover tests, durable retries | Synthetic connector tests; live unverified; browser configuration tested with doubles; additional purchased requirement semantics incomplete |
| 6 Imports/AI | Public HTTPS safety, JSON-LD drafts, import review confirmation, idempotent requests, encrypted admin configuration, synthetic connection probes, request budgets, text AI provider adapters, share inbox and review UI sources | Partial: source-specific captions/transcripts, ingredient parsing, live providers, image extraction, native lifecycle validation |
| 7 UX | Dashboard/start-screen settings, system appearance, native components, localisation, 14-day widget cache/deep links and opt-in local reminder settings/reconciliation | Core dates/DST/cache/links tested; native delivery/rendering/permission/lock lifecycle, accessibility, photography and UI performance unverified |
| 8 Release | Local backup, media-aware JSON/ZIP restore, independent CI configuration, governance and release instructions | Partial: Apple build/signing/TestFlight, demo, screenshots/icons, remaining container advisory triage, full security review, ARM64 runtime, stable releases |

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

- Shell GitHub API returned `Forbidden`; no remote repositories, workflows or releases
  have been created or executed. Intended owner is CLOUDCOOKCH.
- macOS/Xcode 27, iOS simulator/device, Apple developer team, signing profiles and App Store
  Connect credentials are unavailable here.
- No Bring test account/list or AI endpoint credentials were supplied. Tests use synthetic
  connectors and HTTP responses. Automatic Bring writes stay disabled without proof.

These blockers do not explain incomplete independent functionality: shared recommendation preferences, cross-device approval recovery,
admin deletion/extended diagnostics, backup replacement, safe media cleanup, non-recipe archive reconstruction, native validation and release assets
are tracked as remaining engineering work, not falsely labelled credential-blocked.


## Latest verification

97 backend tests and 76 Swift core tests pass. Docker photo upload, leftover exclusion, suggestion approval/replay across restart and JSON/ZIP restore pass. Chromium setup, household/AI/Bring forms, device revocation/password change and JSON/ZIP transfer passed with explicit external-service doubles. Encrypted AI settings persist across Docker restart. Runtime and browser/development dependency audits and source secret scans pass. Container security
still fails: 44 high package matches across 8 unique advisories, no critical matches.
See VALIDATION.md and its recorded artifacts. Distribution workflows require the protected
environment variable `RELEASE_ACCEPTANCE_VERIFIED=true` and are not enabled by these results.
