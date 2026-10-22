# Sync-status UI review

Date: 2026-10-22. The fresh read-only finish reviewer returned **ship within the
reviewed sync-status hardening scope** after confirmation of one material fix:
**1 resolved, 0 partial, 0 unresolved**, with no additional scoped finding. The verdict
scores the corrected Copy/Export targets. It does not establish whole-product readiness,
a diagnosis or repair of the user's deployed failure, publication, or security acceptance.

## Scope and authority

The user reports that PWA/server sync is not working, missing updates across the app
while the indicator says synced. No live deployment, deployed image or diagnostic report
was accessed here. The actual deployment cause remains **unknown**. The investigation
reproduced client defects locally; those defects are evidence for the changes, not proof
that they caused this user's deployment symptoms.

This is an ordinary Operate refinement. PRODUCT.md, DESIGN.md and the PWA surface brief
remain the design authorities. The original peach and lowercase wordmark, Flo and existing
After Dark/Sunday themes, system typography, solid forms, glass navigation and six primary
destinations are preserved. There is no new approved comp, seed, design card, replacement
visual world, API/schema change, migration or native change.

The header now distinguishes unchecked, pending, failed and blocked states. An empty
outbox cannot by itself produce “Up to date”: failure takes precedence and a successful
complete run is required. The existing alert links to Settings; incomplete catch-up
explains that local edits are kept and asks for retry. Copy stays literal in English
and German.

Record catch-up must reach both the advertised server head and revisions returned for
accepted writes. Bounded incomplete catch-up reports failure and can resume from committed
pages. Sync GETs receive fresh query nonces and no-cache/no-store directives; this resists
ordinary URL-keyed caches but does not certify a proxy that ignores query strings. Normal
record delivery/pull now precedes queued import delivery/polling, preventing a failed
import from starving record exchange. The model coalesces the complete sync and household/
planning refresh operation. Local pending work, rejected edits and queued sources remain
recoverable. See [troubleshooting](../SYNC_TROUBLESHOOTING.md).

Settings moves “This device” below the household/account section so sync and diagnostics
are easier to find. “Check sync connection” produces a labelled read-only selectable
report, with busy feedback, Copy/copied feedback and JSON export. Counts, cursors,
attempted phase, last complete success, session/device/history match booleans and
allowlisted errors help compare local and server progress. The report excludes household
content, source URLs, household/device/session IDs, history proofs, prompts, passwords and
credentials. It is separate from the content-bearing private recovery archive produced by
“Export unsynchronised work”. Collecting a report does not clear the outbox or rebuild
browser storage; probe failures remain visible.

## Review and confirmation

The initial full review found **FIX1**: Copy/Export targets were 40px high. The builder
added a scoped 44px minimum height to buttons immediately following the report textarea,
rebuilt and recaptured all six views. The same fresh reviewer confirmed the fix from final
source/captures and supplied geometry assertions and returned the disposition above.
No further scoped UI finding was reported. This is a bounded fix confirmation, not a
second whole-product acceptance review.

This separate documentation handoff read PRODUCT.md, DESIGN.md, the PWA surface brief,
README.md, docs/IMPLEMENTATION.md and the troubleshooting guide; inspected App.tsx,
Settings.tsx, model.tsx, sync-status.ts, sync-diagnostics.ts, sync.ts, api.ts, store.ts,
styles.css, i18n.ts and scripts/sync_status_browser_smoke.py; and opened all six final
captures below. It checked the supplied frontend/browser/build logs and before-fix proof.
It did not rerun tests, recapture screens or run another browser pass.

The captures retain the incumbent hierarchy, materials and typography. German text wraps
at 390px/320px. The 320px full-document image does not paint textarea content; the paired
320×740 viewport capture clearly paints the selected report. The reviewer accepted this
combined evidence. Phone full-document captures retain fixed navigation at the original
viewport position, creating an overlaid document band. That capture behavior alone does
not demonstrate an inaccessible last item. Static images do not establish motion,
screen-reader delivery or physical-device behavior.

The context launcher and detector are absent; no launcher, automated design detector,
design-hook or plugin-schema pass is claimed. The Impeccable skill/document reference
was available to this documentation handoff, while the shipped specialist definition was
not used; no shipped specialist pass is claimed. Existing context was read directly.

## Genuine capture record

These are actual Chromium renders of the real PWA using a synthetic household. Desktop
viewport is 1440×1000, phone 390×844 and narrow phone 320×740. Full-document images are
taller than their viewports. The stale pull and 503 responses are explicit injected
test faults, not observations from the user's deployment.

| Capture | State and image size | SHA-256 |
| --- | --- | --- |
| [Desktop Settings](../../.impeccable/review/sync-status/sync-report-desktop.png) | English Flo, failed/incomplete sync, copied report; 1440×4909 | `bfc681fe6b632b4b1770aa45ddee137faf3285e12af29c27de8a987d42c87eb9` |
| [German phone Settings](../../.impeccable/review/sync-status/sync-report-phone-de-dark.png) | After Dark, failure and diagnostics; 390×6276 | `ad3754bbf7abca6fbc9cf864f3ea3af8c0f40969d40aefde9200d47af34611a9` |
| [German 320px Settings](../../.impeccable/review/sync-status/sync-report-phone-320-de-dark.png) | After Dark, full-page layout; textarea paint limitation above; 320×6716 | `d12e871240b17804552c0e54fb842df954751a0bcb5e2eea4b0ad59eb57d4d7c` |
| [Desktop report detail](../../.impeccable/review/sync-status/sync-report-detail-desktop.png) | Report text and corrected Copy/Export actions; 1440×1000 | `f6ced9cfc94778b22bb4e72a4c6dd891a7cf7029f4164c0b980ab61670aba0cb` |
| [German phone report detail](../../.impeccable/review/sync-status/sync-report-detail-phone-de-dark.png) | Selected/selectable report; 390×844 | `483ad51ce5ffe0e496a3d3e0f84a44a53a0c705c0161493bcdec3261a1e903d9` |
| [German 320px report detail](../../.impeccable/review/sync-status/sync-report-detail-phone-320-de-dark.png) | Selected report painted at narrow viewport; 320×740 | `69aaed78d5ca82c3484b0be804d9406279297fbfe3f1ae80eb47f187a446de2e` |

## Supplied validation and limits

`build/sync-investigation/before-fix.log` records two reproductions from the preceding
source: a stale empty page returned success with server head 5/client cursor 0, and one
failing queued import stopped all outgoing/incoming household records. Frontend regressions
cover known-revision completion, interrupted catch-up/resumption, stale reads, import
starvation, status precedence and report redaction. `build/sync-investigation-tests.log`
confirms **66 passing frontend tests**.

`build/sync-status-browser.log` records a pass against a real server/SQLite with two
independent browser cookie contexts: recipe/calendar/pantry exchange, offline Save/reload/
replay, expired-session rotation, stale-page rejection, failed/no-outbox status and redacted
copyable English/German diagnostics. Script inspection confirms Copy/Export height
assertions of at least 44px on desktop and 390px, Axe WCAG 2 A/AA and 2.1 AA checks on
desktop/390px, and horizontal-overflow/layout evidence at 320px. **No 320px Axe run is
claimed.** `build/sync-regression-browser.log` also records the existing full PWA regression
pass, including concurrent edits, deletion/rejected-copy recovery and explicit import review.

The final `build/sync-status-pytest.log` confirms **425 passing backend tests**, including
four added CI-helper nonce-pattern regressions, with one known Starlette warning. The
implementation handoff also supplies Ruff lint/format across 118 files, mypy across 50
source files and generated OpenAPI drift checks. The CI outage classifier accepts an
optional canonical UUIDv4 nonce only alongside the same confirmed local HTTPS failed
request; window errors and unhandled rejections remain fatal. This is test-helper behavior,
not a runtime API/schema change. `build/sync-status-build.log` confirms the final frontend build/type check;
the main bundle exceeds 500kB, a disclosed nonblocking size warning. These are supplied
results, not new runs by the reviewer or documenter.

No live deployment was diagnosed or repaired. Live provider behavior, physical iPhone/
Safari, native UI, every theme/state and complete manual accessibility remain outside this
evidence. Exact-source CI and publication are pending at this handoff; earlier release
evidence does not certify this tree. No security audit or whole-product acceptance is claimed.

## Preserved design-document drift

DESIGN.md retains five-destination prose, older navigation/calendar/layout measurements
and historical system-only appearance guidance. The project-owned design.json snapshot
retains five-destination and historical responsive/calendar statements, alongside later
Flo/After Dark/Sunday guidance. The surface brief also contains historical system-following
appearance text. These snapshot conflicts are not instructions to undo the six-tab shell
or theme library. This handoff only appends current authority/evidence to the surface brief
and preserves DESIGN.md/design.json without repair.

Preserved SHA-256: DESIGN.md
`a1ed87ec5c749605e329f1fbc79860d26f823d295e132f7f4788177dc6b97af8`;
`.impeccable/design.json`
`b9ccc9ccbe9a0e0759c5e5bd8dc467038edba10a4b3d0dadb434d09659d57d99`.
