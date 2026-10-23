**Household accounts and RBAC, 2026-10-23 — candidate `poc-20261023.5`, unpublished:**
Admin-managed accounts in console Account → Household users; User (default) and Admin roles.
Migration 017 promotes the existing shared login and attaches existing sessions to it.
Separate Argon2 passwords, live role/active checks, account-scoped session/password operations,
role/password/disable revocation and transactional last-admin protection are implemented.
All admin APIs plus household and integration configuration reject regular users. Read-only
app AI/status and household counts keep shared imports and diagnostics available; PWA hides
admin controls for regular users. Account secrets are omitted from non-secret exports.
Local recovery restores the original account as an active admin and revokes all sessions.
Local edits during an active synchronization schedule a follow-up pass without delaying
the durable save; a delayed-account-refresh browser regression covers rejected-copy recovery.

Validation: **479 backend / 81 frontend tests pass**, plus Ruff lint/format, mypy,
OpenAPI drift, Prettier, TypeScript and production frontend build. Real Chromium account
management and regular/admin PWA flows pass, including mobile Axe and immediate revocation.
Existing console EN/DE/200% text-zoom, PWA offline/two-device and AI-import browser suites pass
with synthetic household/provider data. The new account browser suite is included in CI. Docker build/smoke is blocked by Alpine
package-index HTTP 403; no container publication, live installation or physical-device test
is claimed. The independent native contract pin is refreshed for this additive API;
existing native wire fields remain unchanged. Native account-management UI is outside this pass.

# Implementation checklist and evidence

**Ingredient editing and compact pantry, 2026-10-23 — container image `poc-20261023.5` available:**
Combined source `7054a06` retains ingredient source `0ec966d` unchanged. Exact-source
CI `39984576734` passes all six gates on attempt 2 (479 backend/81 frontend), including
Chromium/WebKit; fresh AMD64/ARM64 image/security/runtime checks pass. Anonymous public
pull and same-volume `.3` → `.5` 5152 upgrade with offline ingredient Save/reload/sync and
pantry exclusion pass. GitHub release creation returned HTTP 500 after successful image
push/attestation, so prerelease metadata/assets are pending; `.4` was never published.
See [durable image evidence](validation/github-ingredient-preview.json).

The PWA recipe editor offers native common-unit choices, retained imported/custom units,
optional local pantry/other-recipe name suggestions with typo matching, and free new names.
Explicit recipe Save, original text, quantities, drafts and outgoing sync remain intact.
No automatic pantry creation, historical rename/merge, guessed unit conversion or Bring
ledger mutation. Pantry rows are denser with decorative food emojis and a generic fallback.
This ingredient extension changes no native/API/database identity or contract. The
combined release separately includes household-account migration 017.

Supplied implementation evidence: **472 backend / 81 frontend tests pass**, Ruff check/format,
mypy, OpenAPI drift, TypeScript/build, Prettier, artwork and licence checks. Real Chromium
ingredient, offline/two-device PWA, UX, AI-import and food-setup suites pass with synthetic
providers; ingredient coverage includes canonical/custom names and units, offline Save/reload/
sync, original text, no phantom pantry, keyboard/trusted tap, pantry toggles, EN/DE, three
themes, Axe and 1440/390/320 widths. A bounded self-check corrected alignment and narrow
field stacking before an independent read-only review returned **ship, zero material findings**.
The documenter inspected source, review and four genuine screenshot copies; no tests or
browser workflows were rerun during documentation.

**Bounded nonvisual follow-up:** the original review/captures record `469d83d`; release
source `0ec966db645fcc105c6e897e417667392ad0bc48` is now merged through PR #20. The four-file
diff from `59e5efd` guards own-property emoji lookup for `__proto__`/`constructor` and
resets/guards combobox active selection when shared household options change. Supplied
follow-up evidence reports 81 core tests, build, Prettier, Ruff and real Chromium passing,
including a focused-combobox server-sync race and prototype-name fallback regression.
The documenter inspected the diff, `/tmp/mealf-ingredient-guard-browser.log` and the same
reviewer's ship addendum without rerunning checks. No additional material finding or
recapture was required; no CSS/layout/copy/artwork changed and all seven original PNGs
remain byte-identical. This follow-up does not imply a new backend/full-regression pass.

The ingredient-only CI `39983929824` was cancelled by the concurrent account merge.
Combined exact-source CI `39984576734` and WebKit ingredient checks now pass; no local
WebKit pass is claimed. The image is available as `.5`; `.4` was never published.
GitHub prerelease metadata/assets remain pending after the upstream HTTP500.
Live AI/Bring!, physical iPhone/Safari and full-product acceptance remain unverified.
Context/detector attempts exited 127; no hook/schema/shipped-specialist pass is claimed.
DESIGN.md/design.json remain byte-identical historical snapshots; navigation/layout/type/
theme drift is reported without repair. See [behavior](INGREDIENT_EDITING.md) and
[review, provenance and limits](validation/ingredient-picker-review.md).

**Pantry and food taste setup, 2026-10-23 — published as `poc-20261023.3`:**
release source `327fcb3`; UI began at `58c5930` plus a scoped ≤360px pantry correction.
Adds the canonical 24-staple EN/DE catalogue, fresh-household Today invitation, permanent
Pantry picker, twelve resumable taste cards, shared revisioned profile/outgoing queue and
frozen preferences on new Recipe ideas requests. Import uses concise disclosure plus
Prepare AI preview; personal ChatGPT consent and explicit recipe Save remain separate.
Migration 016 and non-secret export v4 preserve old import/archive compatibility.

Implementation-agent evidence: **472 backend / 76 frontend tests pass**, Ruff lint/format,
mypy, Prettier, TypeScript/build, OpenAPI drift, original-artwork and licence checks.
Real Chromium food setup, AI imports, source photos, Recipe ideas, PWA UX and sync-status
suites pass with synthetic provider HTTP, Axe, EN/DE/all three themes, 1440/390/320 widths,
offline Save/reload/sync, draft resume and actual-adapter preference payload/no-autosave
checks. The bounded independent manual review initially found one P2 German-label issue;
the narrow correction resolves it: **ship, 1 resolved / 0 partial / 0 unresolved**.
A subsequent nonvisual sync fix blocks profile PUTs on backwards server revisions and
archives pending food state during explicit history recovery without automatic replay;
a meaningful regression test brings the frontend total to 76. UI/CSS/captures are unchanged.
The documenter ran no browser/tests. See [behavior](FOOD_SETUP.md) and
[review/provenance and limits](validation/food-setup-review.md).

[Server PR #16](https://github.com/CLOUDCOOKCH/mealf/pull/16) is merged at `327fcb3`.
All six exact-main CI jobs `39973942662` and publication `39975217859` pass. Both native
architecture images pass unsuppressed HIGH/CRITICAL scans and startup/restart/persistence/
export-restore checks. Six public checksums/config identities/SBOMs and anonymous pull pass.
The local published `.2` → `.3` upgrade remains unverified: initial old-image launch hit
ENOSPC; after removing an unused verification image, the workspace went offline before
the rerun result. Local construction also encountered blocked Alpine egress. No local
upgrade/build pass is claimed; see [exact evidence](validation/github-food-setup-preview.json).
Vite serves the catalogue (200) and denies unrelated requirements (403).
The native contract is pinned at `58c5930` in merged companion PR #4; local contract and
296 locale checks pass. Exact native main CI `39971563258` passes core, formatting,
Xcode and simulator at `1b2f3d3`. No native food UI, live AI/Bring!, physical iPhone or
production-v1 acceptance is claimed.
DESIGN.md/design.json remain byte-identical historical references with existing drift.

**Everyday navigation and quick planning, 2026-10-23 — published and verified in
`poc-20261023.2`:** four primary tabs (Today, Plan,
Recipes, Shopping), persistent account → Settings → Back, and Shopping → Pantry → Back.
Internal route IDs, deep links, preferences, API/database/native contracts and durable
local work remain compatible. Empty Plan slots open title search with rating-first
recipes and guarded one-tap assignment using saved household/recipe portions. Separate
Meal options retains date/category/portions/leftovers/recurrence; quick leftovers retain
the real ID and cap available portions. Compact day meals, actual-occurrence week marks,
a separate mobile sync-status row and readable inactive nav ink complete the extension.
Cooking mode remains outside this pass. Original artwork, palettes and three themes stay.

Local verification: 459 backend / 70 frontend tests pass, with the backend run configured
for EN/DE OCR via `TESSDATA_PREFIX=/workspace/Mealf/mealf-server/build/ux-ocr` (an initial
unconfigured run had eight OCR-data failures). Ruff lint/format, mypy, Prettier, frontend
types/build, OpenAPI drift, unchanged pinned iOS schema, brand-byte and licence checks
pass. Actual Chromium UX covers navigation/Back/Pantry selected state, picker search and
empty state, default portions, offline double activation/reload/once-only sync, custom
portions/recurrence and leftover ID/cap. Core PWA, layout/drag/safe-area/date geometry,
shopping/sync/themes, imports/OCR/AI/ideas/source photos/ChatGPT/push regressions pass
with synthetic integrations. Final theme/Axe checks pass after inactive nav contrast
was corrected using semantic ink. A fresh independent manual specialist equivalent
reviewed all 21 captures and sampled sources: **ship at this scope, no material fixes**.
Six unmodified captures and checksummed provenance are retained in documentation.

All six [exact-main CI jobs](https://github.com/CLOUDCOOKCH/aircooker-server/actions/runs/39961500266)
pass at `fe2c53a4f18cdd6b9f2821e98f2ce3e0d9368f34`, including Chromium/WebKit and both native
architecture build/security/runtime checks. [PR #15](https://github.com/CLOUDCOOKCH/aircooker-server/pull/15)
is merged. The [publication run](https://github.com/CLOUDCOOKCH/aircooker-server/actions/runs/39962376171)
passes fresh image gates; the [release](https://github.com/CLOUDCOOKCH/aircooker-server/releases/tag/poc-20261023.2)
index is `sha256:8bf01701628da7d7555455075ae6f37ce2f15887619e73d14542a4c177c14ca3`.
Six public asset checksums, exact-source Compose/OpenAPI, both native config identities
against build logs/scans, zero HIGH/CRITICAL findings, SBOMs, provenance, preview alias and
anonymous pull pass. A published .1-to-.2 same-volume 5152 upgrade preserves identity,
session, history, recipes and the 400 g projection. One offline double-activation meal
survives reload and syncs once, producing the expected 600 g projection. Four EN/DE routes,
account diagnostics, nested Pantry/Back and narrow cached offline Shopping pass in the
pulled image. See [exact publication evidence](validation/github-quick-planning-preview.json).
There is no local WebKit binary; the engine evidence comes from CI. Launcher/detector
are unavailable (attempt exited 127); no shipped specialist/schema pass is claimed.
Physical iPhone/live-service acceptance remains open. See [screen guide](PWA_UX.md) and
[bounded review, capture matrix and exact limits](validation/quick-planning-review.md).
DESIGN.md and its sidecar are preserved byte-for-byte; their older navigation/layout/
type/theme descriptions remain documented snapshot drift, outside this extension.

**Security corrections, 2026-10-23 — published and verified in `poc-20261023.1`:**
IP-rejected native/PWA/admin login attempts no longer consume the shared household budget;
per-IP admission, distributed protection and expiry remain. Recipe/AI quantities are bounded
before fixed rendering across ingress, scaling, shopping and legacy local reads. Original
Decimal representations survive replay; unsafe records, offline edits/drafts/checkpoints
and rejected cached ideas are retained. The canonical API documents the numerical bound.
Local verification: 459 backend and 70 frontend tests pass; Ruff lint/format, mypy, OpenAPI
drift, PWA types/build pass. Chromium AI ideas regression passes including offline reviewed
Save/reload/sync, EN/DE recovery and invalid legacy-cache retention without paid retries.
An independent read-only bypass/regression review found no reportable surviving route.
No production data, external credentials or live provider/Bring! calls were used.
[Server PR #14](https://github.com/CLOUDCOOKCH/aircooker-server/pull/14) is merged.
All six [exact-main CI jobs](https://github.com/CLOUDCOOKCH/aircooker-server/actions/runs/39954293982)
pass at `8ce57c7ad43a5a5b3498cb381af0f0865d8c20bf`, including Chromium/WebKit, both native
architecture builds/runtime tests and unsuppressed security scans. The [publication run](https://github.com/CLOUDCOOKCH/aircooker-server/actions/runs/39955574162)
also passes with fresh scans and runtime checks of the actual two published images.
The [public release](https://github.com/CLOUDCOOKCH/aircooker-server/releases/tag/poc-20261023.1)
has index digest `sha256:b1ec2a44c43bf059638a1f8ed59d108f2b0b6d5c75605f92a63d5d6c332282a1`.
Six public asset checksums, exact Compose/OpenAPI, both native image config IDs versus
build logs/scans, zero HIGH/CRITICAL findings, SBOMs, source/version labels, matching
`preview` tag and anonymous pull pass. A disposable published .10-to-.1 same-volume
5152 upgrade preserves identity, active session, history, recipes and the 400 g projection.
An old `1.00`/zero-exponent mutation returns its original receipt without changing history.
Actual packaged model/rendering guards reject both expansion forms, and forty single-IP
login attempts leave a fresh-IP correct login available. Published EN/DE narrow-phone
navigation and cached offline shopping pass. The optional local Docker build was blocked
by the environment's Alpine-download HTTP 403; the native CI and published-image checks
provide the completed Docker validation. Physical iPhone/live services remain unverified.

Verification commands: `python -m compileall -q src`, `python -m mypy src/mealf
--ignore-missing-imports`, `npm run typecheck`/`build` pass; focused security tests and
`python -m pytest -q` pass (459), `npm test` passes (70). Ruff lint/format, Prettier,
`python scripts/export_contract.py --check`, licence/artwork checks and the real
`scripts/recipe_ideas_browser_smoke.py`/`scripts/pwa_browser_smoke.py` pass.

**Recipe ideas diagnostics, 2026-10-22 — published and verified in `poc-20261022.10`:**
allowlisted English/German provider errors survive the durable worker and cached PWA
failure, with explicit recovery and no automatic paid retries. Gemini display names with
whitespace are rejected before configuration is saved; API ID hints appear in the PWA and
administration. Raw gateway errors are distinguished from structured provider errors.
The connection test now reports known provider 5xx failures as 422 configuration-validation
errors with allowlisted codes; it preserves 429 quotas, genuine server failures and explicit
paid retries. Synthetic proxy replacement, transport failures, safe logs and browser EN/DE
recovery are covered. The supplied Cloudflare HTML confirms a missing readable API response;
historical refused connections and a current healthy direct origin do not establish the
live AI failure's cause. No proxy or household configuration was changed.
The user reports that the small connection probe succeeds with structured output disabled;
the same stored ideas request remains failed with the old coarse provider code. A fresh,
explicitly approved batch is needed to diagnose generation. No credentials or live data
were accessed. See [configuration and troubleshooting](RECIPE_IDEAS.md).
Local verification: 445 backend tests, 67 frontend tests, build/type/format, Ruff, mypy,
OpenAPI drift, Chromium proposal/error/recovery and administration regressions pass.
See [bounded review and genuine capture provenance](validation/recipe-ideas-errors.md).
All six exact-main-source CI jobs pass at `0f1b88e7`, including 445 backend tests per
architecture, 67 frontend tests and full Chromium/WebKit checks. A matching digest-pinned
official Playwright test image replaces repeated slow WebKit dependency downloads;
application assertions and production/security gates are retained. Both fresh native image
scan/runtime executions, six public asset checksums, image identities/SBOMs, provenance and
anonymous pull pass. A published .9-to-.10 same-volume 5152 upgrade preserves identity,
active session, sync history, recipe and shopping quantities. The packaged API preserves a
redacted provider failure without saving a recipe. Physical iPhone and live generation
remain unverified. See [exact publication evidence](validation/github-ai-diagnostics-preview.json).

**Whole-PWA UX rework, 2026-10-22 — published and verified in `poc-20261022.9`:**
Home leads with meals and explicit actions; Calendar has compact date/view controls and
readable multi-day cards; Recipes has labelled import/create, search/rating sort and
section links. Optional editor metadata folds without losing values, with persistent
draft feedback and a sticky Save bar. Imports progressively expose text/file inputs.
Settings groups configuration behind native disclosures; Pantry and Shopping share the
same hierarchy. Original brand assets, all themes, six destinations, native/admin/API/
database/sync contracts and existing offline/review/ownership behaviors are retained.
Local 425 backend/66 frontend tests, type/format/Ruff/mypy/OpenAPI and all Chromium
PWA/import/AI/photo/ideas/push/shopping/sync/layout regressions pass. Provider transports
are synthetic. Fresh full UI review found one misleading unconfigured/queued Shopping
state; a readiness-aware UI fix was scored 1 resolved, 0 partial, 0 unresolved. The verdict
is ship at that listed-fix scope, not product acceptance. Local WebKit binary is absent;
final PR and exact-main CI supply passing Linux WebKit layout/theme/OCR/offline evidence.
All six exact-main-source jobs pass at `76fe7995`. Both fresh native image scan/runtime
gates, six public asset checksums, image identities/SBOMs and anonymous pull pass. A
published .8-to-.9 same-volume 5152 upgrade preserves identity/session/history/recipe/
shopping data and exercises the new Settings disclosures, report and EN/DE offline
navigation. Initial PR theme-test navigation assumptions were corrected without weakening
assertions. Physical iPhone/live-service acceptance remains open. See [guide](PWA_UX.md),
[review](validation/pwa-ux-review.md) and [exact publication evidence](validation/github-pwa-ux-preview.json).

**Sync investigation, 2026-10-22 — published and verified in `poc-20261022.8`:**
Reproduced old false-success acceptance of a stale pull and import failures starving all
record exchange. Header failure/unchecked states, required revision checks, fresh sync reads,
record-first delivery, coalesced full sync and allowlisted content-free diagnostics are
implemented. Local checks pass 425 backend/66 frontend tests, types/format/Ruff/mypy/OpenAPI;
real browser two-device/offline/expired-session/stale-page/503/report checks pass. API and
canonical sync schema are unchanged, so the independent native contract is deliberately
retained. The actual user's deployed failure remains unconfirmed until their report is
available. All six exact-main-source CI jobs pass at `708365b0`, including Chromium/WebKit
and both architecture security checks. Both fresh native publication image scan/runtime
gates, six public asset checksums, manifest/config identities/SBOMs and anonymous pull pass.
A published .7-to-.8 same-volume 5152 upgrade retains identity/session/history/recipe and
shopping quantities; published Settings diagnostics, EN/DE navigation and cached offline
shopping pass. Physical iPhone and live deployment acceptance remain open. See
[safe investigation and limits](SYNC_TROUBLESHOOTING.md) and
[exact release evidence](validation/github-sync-preview.json).

**Recipe ideas, 2026-10-22 — published and verified in `poc-20261022.7`:**
Home/Recipes offers ingredient-based or surprise generation using configured household AI.
Three complete proposals require editor review/Save; no automatic library/calendar/Bring!
changes. Migration 015, idempotent delivery, pinned consent, recovery without duplicate
billing, redaction and preview retention are covered. Local validation passes 421 backend
and 59 frontend tests, Ruff/mypy/OpenAPI, build and real Chromium ingredient/random/offline
review-save-reload-sync/Axe using provider HTTP doubles. Live provider/physical iPhone remain
unverified. All six exact-main CI jobs pass at 74c1c925, including both native architecture
build/runtime/security gates and Chromium/WebKit regressions. Both fresh publication image
gates, public hashes/config identities/scans/SBOMs/anonymous pull and published .6-to-.7
same-volume 5152 upgrade pass. See [exact evidence](validation/github-recipe-ideas-preview.json).
Explicit user scope addition: [guide](RECIPE_IDEAS.md), [decision](adr/016-creative-recipe-ideas.md).
Native UI remains unchanged; the deliberate contract refresh passes independent CI.

**Shopping navigation, 2026-10-22 — published and verified in `poc-20261022.6`:** Shopping list is the sixth
primary PWA destination on desktop/mobile. Existing shortcuts select the same tab.
English/German labels, keyboard activation, one current destination, 320px target/label
bounds, manual sync/manual-item preservation and cached offline reopening pass real
Chromium checks with a synthetic Bring transport. Local validation passes 392 backend
and 59 frontend tests, build/type/format, Ruff/mypy/OpenAPI and mobile layout checks.
All six exact-main-source CI jobs pass at c403651, including Chromium/WebKit and both
native security gates. Both fresh native preview image gates, public assets/config checks,
anonymous pull and a published .5-to-.6 same-volume 5152/session/history/PWA/offline
upgrade check pass. See [exact evidence](validation/github-shopping-navigation-preview.json).
Physical iPhone/live-service acceptance remains open. An isolated CI-only follow-up for
native WebKit outage diagnostics is under validation; it does not change this release's
app/API/storage behavior or suppress the published source's test assertions.

**Recipe photos — published and verified in `poc-20261022.4`:** the original peach fills
missing/unreadable recipe pictures across the PWA. Public URL imports try source metadata
images through bounded pinned-HTTPS fetching, store a local sanitized image and retain
attribution and incomplete AI drafts through explicit review/Save. Cached pictures work
offline; unavailable pictures remain honest placeholders. Migration 014 and the additive
optional import `source_photo` field preserve existing recipe/sync fields; native is unchanged.
See [behavior and limits](RECIPE_PHOTOS.md). Live sites/providers and physical iPhone remain
unverified. All six exact-source CI jobs pass at e47b107: 383 backend tests per architecture,
55 frontend tests and real Chromium/WebKit regressions. Both fresh native image gates,
six public checksums/config identities, anonymous pull and published .3-to-.4 same-volume
5152 upgrade/OCR/restore pass. See [exact release evidence](validation/github-source-photos-preview.json).

**Shopping/Bring! visibility — published and verified in `poc-20261022.3`:** Home, Calendar
and Settings open a read-only current-week requirement list with quantities, ownership states,
pantry exclusions, server job/errors and a manual Sync to Bring! action. Cached snapshots
remain useful offline with a stale/local-edit warning. An explicit dedicated-test-list
check now runs inside the container worker; no terminal/helper is needed. Reports remain
scoped, expire and fail closed on missing UUID acknowledgements. See [shopping guide](SHOPPING.md).
All six exact-source CI jobs pass at 74c76bf: 366 backend tests per architecture, 54 PWA
tests and real Chromium/WebKit regressions. Both fresh native image gates, six public
asset checksums/config identities, anonymous pull and the published .2-to-.3 same-volume
5152 upgrade/OCR/restore pass; synthetic purchased ownership history is preserved. See
[exact publication/upgrade evidence](validation/github-shopping-preview.json). Live Bring!
and physical iPhone behavior remain unverified; native is unchanged.

**Personal ChatGPT imports — published and verified in `poc-20261022.2`:** the supported
open-source OAuth/PKCE loopback helper pairs a personal account with one authenticated
mealf session. Encrypted server credentials, verified signed tokens, account model discovery,
serialized refresh, explicit per-import background consent and a pinned durable text-only
request lead to the existing editable preview and Save. No household pooling, browser token
storage, unofficial consumer endpoints or paid API fallback is used. Existing household
providers and local photo OCR remain available. See [setup and limits](CHATGPT.md),
[architecture](adr/015-personal-chatgpt.md) and [bounded UI review](validation/chatgpt-ui-review.md).
All six exact-main CI jobs pass at d34d65f: 349 backend tests per architecture, 52 PWA
tests and real Chromium/WebKit regressions. The standalone helper passes on Windows
Python 3.10/3.12. Both fresh image gates, six public asset checksums/config identities,
anonymous pull and the published .1-to-.2 same-volume 5152 upgrade pass. Identity/session/
recipe/photo/history, offline replay, real EN/DE OCR previews and clean archive/photo restore
are preserved. See [exact release evidence](validation/github-chatgpt-preview.json).
Live OpenAI registration/allowance/inference and physical-iPhone checks remain unverified.
The retained native repository is deliberately unchanged: additive API-v1 routes do not
alter its existing sync contract; this connection interface is PWA-only for now.

**PWA v1 readiness:** feature scope is frozen in [V1_READINESS.md](V1_READINESS.md).
The candidate/stable workflow now requires exact main-source CI, fresh native scans and
runtime checks, publication of verified bytes, matching package/API versions and separate
RC/stable channels. Stable distribution additionally requires every machine-readable
acceptance gate and protected operator approval. The register honestly retains open
recovery/deletion/resource work and blocked physical/live-service/security-audit evidence.
SQLite caps, redacted storage failures, durable-worker retry/shutdown, verified atomic local
backups and interactive offline deletion now have local regression coverage. Current local
validation passes 309 backend/51 frontend tests, type/lint/contract/brand/licence checks and
real PWA/OCR Chromium flows. All six exact-main-source CI jobs pass at bca0dbc, including
309 backend tests on each architecture, 51 frontend tests and real Chromium/WebKit checks.
`poc-20261022.1` is published: both fresh native scans/runtime/operator gates, public pull,
six asset checksums/config identities and the published .10-to-.1 same-volume 5152 upgrade
pass. Existing identity/session/history and idempotent offline replay survive; real EN/DE
OCR stays preview-only and a .10 ZIP restores its recipe/photo into a clean .1 install.
See [local evidence](validation/v1-readiness-local.json) and
[publication/upgrade evidence](validation/github-v1-readiness-preview.json).
Guided recovery, expanded resource/recurrence acceptance, the dedicated security review,
physical/live-service/pilot evidence and a real RC rehearsal remain open. No stable release
or production acceptance is claimed.

**AI recipe import — feature branch integrated with the published photo/theme/calendar work:**
Encrypted provider profiles and explicit per-model input capabilities support bounded AI
image/PDF imports and Gemini video requests. Website metadata precedes AI; consent binds
the displayed provider destination. Every result remains an editable preview until saved.
The existing camera/chooser retains local EN/DE OCR and its text-only optional-AI privacy
contract. Migration 011 adds the AI tables without changing released migration 010 or
legacy replay receipts. Regression tests preserve queued photos through upgrade and prevent
cancelled attachment uploads from creating imports. Local combined validation passes 279
backend and 50 frontend tests, Python/TypeScript checks, production build and contract/brand/
licence checks. See [AI import configuration and limits](wiki/AI-Recipe-Import.md) and
[merge validation](validation/ai-recipe-import-merge.json). Original branch-only evidence is
retained separately in validation/ai-recipe-import.json. Cloud responses in tests are
synthetic; live providers/models, physical Apple devices and the updated native contract
remain unverified. Merging source does not publish a new container release.

**Photo recipe import, 2026-10-21 — published and verified in `poc-20261021.10`:**
PWA Import recipe offers Take photo and Choose image. Atomic image/job persistence,
metadata-stripped upload and bounded local EN/DE OCR produce editable previews; only
explicit Save creates a recipe. Unclear text stays correctable, with manual fallback.
Optional text AI requires consent and never receives image bytes. Terminal-source
retention preserves replay proofs; unused media remains under the existing quota.
All six source CI jobs pass at db207a2: 240 backend tests per architecture, 45 web tests,
real Chromium/WebKit OCR/offline-save/reload and Axe. The headless WebKit photo test
explicitly models OS push unavailable; separate synthetic reminder tests verify the
permission boundary, and Settings avoids native subscription discovery before consent.
Both fresh native image scans/runtime gates, six public checksums/config identities,
anonymous pull and published .9-to-.10 same-volume 5152 upgrade plus real EN/DE OCR pass.
Native contract pin 32604a1 passes 90 core tests on each platform, Xcode 26.6 builds and
existing simulator flows. Physical camera/iPhone and live AI/push remain unverified;
full product acceptance remains open. See [photo import](IMAGE_IMPORT.md) and
[exact release evidence](validation/github-image-import-preview.json).

**Theme library, 2026-10-21 — published and verified in `poc-20261021.9`:** Settings offers Flo
(existing system light/dark), After Dark (fixed dark romance palette) and Sunday
(fixed light sage/linen). A shared early controller and semantic CSS cover PWA and
console, native fields and browser metadata. Browser-local choice persists offline
and propagates across tabs; storage failures are disclosed. Original PNGs, API and
local/server database identities are unchanged. Real Chromium checks cover native radio
keys, opposite OS modes, early boot, offline reload, admin sharing, denied storage,
contrast and Axe. All six exact-source CI jobs pass, including persistent WebKit with
real backend-outage cached reloads and narrow German controls. Both fresh image gates,
six public checksums, config identities, anonymous pull and published .8-to-.9 same-volume
5152 upgrade pass. Physical iPhone remains unverified. See [theme guide](THEMES.md) and
[release evidence](validation/github-themes-preview.json).

**Mobile calendar and form alignment, 2026-10-21 — published and verified in `poc-20261021.8`:**
Day/3 days/Week selection persists per device. Multi-day columns remain readable and
scroll horizontally. Explicit pointer/touch grips highlight destinations, scroll at
edges and cancel on Escape, pointer cancellation, blur, hide or resize. Tap/keyboard
activation opens the existing move form. Committed moves reuse transactional offline
mutations and recurrence exceptions. Narrow dialog fields stack and date/select widths
are constrained. Local 226 backend/39 frontend tests and full PWA flows pass; Chromium
layout checks exercise actual offline touch moves/reload, pointer edge scrolling,
cancellation, native scrolling and paired control bounds. Chromium/WebKit CI and all
six exact-source jobs pass; both fresh image gates, six release checksums, anonymous
pull and published .7-to-.8 same-volume 5152 upgrade pass. A duplicate tag event
safely skipped image writes. Physical iPhone remains unverified. See MOBILE_CALENDAR.md
and [release evidence](validation/github-mobile-calendar-preview.json).

**Phone PWA viewport fix, 2026-10-21 — published and verified in `poc-20261021.7`:**
mobile fields no longer inherit 12–14px label text, which can trigger iOS focus zoom.
Safari text autosizing and all-edge safe-area layout are explicit. Navigation handles
short touch landscape; dialogs remain inside safe bounds. Local Chromium checks cover
320/390px portrait, symmetric/asymmetric landscape, desktop, field focus, recipe editing
and sheets. Existing 226 backend/39 frontend tests and PWA flows pass. CI adds WebKit
engine coverage; physical Home Screen/keyboard confirmation is still unverified.
All six exact-source CI jobs passed, including Chromium and persistent-profile WebKit
layout tests. Both image scans/runtime gates, public pull, six release checksums and the
published .6-to-.7 same-volume 5152 upgrade passed. See [layout evidence](validation/mealf-phone-layout-local.json)
and [publication evidence](validation/github-phone-viewport-preview.json).

**Peach interaction, 2026-10-21 — tested and published in `poc-20261021.6`:**
shared PWA/console native peach buttons activate a silent hand-swipe/wobble and rotating
EN/DE reactions. Wordmark navigation is separate. Reduced motion, repeated taps, keyboard,
caption bounds and offline use pass Chromium checks. More food innuendo appears in login,
Home and selected empty states; security/help/errors stay literal. Local 226 backend and
39 frontend tests, lint/type/build/contract/brand checks and PWA/admin/push browser flows
pass. Physical Safari/iPhone is unverified; native remains unchanged. See PEACH_EGG.md. All six exact-source CI jobs and both fresh
image gates pass. Public pull, asset/config identities and the published .5-to-.6 same-volume
5152 upgrade pass; see [release evidence](validation/github-peach-preview.json).

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
