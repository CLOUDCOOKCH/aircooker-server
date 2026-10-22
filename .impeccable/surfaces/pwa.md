# mealf PWA operating surface

Mode: Operate. Approved purpose/platform: PWA-first, retaining native code; user confirmation
on 2026-10-21. Preserve the approved native concept and product requirements. Stack choice
is delegated by the master prompt. The confirmed mealf name/asset rebrand applies to the
established glass interface. The explicitly approved palette/voice refresh described below supersedes the former green accent constraint while preserving the glass/system-type world.

Visual authority: existing SwiftUI KitchenStyle/components and the user-approved glass
concept at /workspace/generated_images/exec-d61616a4-31c5-4cbf-8f34-24d3ed52d35f.png.
The image is labelled illustrative; it is not a product capture. Supporting private design
references apply to the conversation only; preserve the approved decisions, not private IDs.

First viewport: Your kitchen heading and compact import/create actions, household civil-week
strip, today's actual meals with one strong food photo when present, accessible empty-slot
actions and visible offline/demo status. Bottom glass five-destination navigation on phones;
adapt content density and navigation on desktop. Existing account data never gains samples.

Current colour: cream/coral/peach light appearance and cocoa/peach dark appearance, with separate raspberry danger roles and warm food photography. Follow system appearance. System UI typography is intentional continuity with
the approved Apple-style operating interface. Glass is reserved for floating controls and
navigation; reading/editing surfaces stay legible. Opaque/reduced-motion fallbacks.

Signature interaction: selecting a civil day updates its meal composition while the week
and navigation remain anchored. Direct create/import, recipe-to-calendar transitions and
clear review-before-apply outrank ornament. No marketing hero, made-up statistics or sample
data masquerading as a real household. Explicit isolated demo can use original artwork.

Implementation contract: durable IndexedDB records/outbox, cookie-based sessions without
browser-stored secrets, server-ordered sync/tombstones/proofs and clear recovery states.
Browser limitations are disclosed in PRODUCT/ADR 010. Build the functioning app, inspect
desktop/mobile together and run the skill finish review/documentation after the bounded
implementation/verification passes. Context launcher is unavailable; existing project
sources and skill resources are the fallback. No design selection is reopened.

Historical brand-delivery handoff before the palette refresh, 2026-10-21: both original PNGs were received in a ZIP and preserved in
`assets/brand/originals/`. The supplied peach and lowercase wordmark replace the interim
utensil/text lockups across the PWA and console. Only fully transparent margins, proportional
output sizes and installation canvases change; no artwork is redrawn or recoloured.
`Brand` uses a decorative 32px peach, 8px gap and 104px image wordmark; compact footer
sizes are 20px/6px/60px. At that historical scope, green controls, system type and glass were retained; the later approved palette refresh replaces the green accent roles.
Versioned touch/favicon/manifest/maskable icons and old icon URLs use the peach. Stable
manifest/storage/session identities preserve household/offline work. Native artwork is
unchanged by this server release. See [branding](../../docs/BRANDING.md) and the
[manual artwork review](../../docs/validation/mealf-artwork-review.md). Five genuine
desktop/phone EN/DE light/dark captures record the delivered brand; offline delivery and
accessible names are tested. Historical name-only/PWA reviews retain their original scope.
The implementation-agent manual review claims no unavailable launcher/detector, plugin
schema, design-hook or independent specialist pass. Physical iPhone/icon refresh is unverified.

Historical reminder handoff, 2026-10-21: Settings includes optional per-device meal reminders within
the existing solid settings surface and approved green/system-type direction. Preserve the
household time zone, explicit connect/enable steps, labelled category/time controls and
separate save/test/retry/disconnect actions. Local preference drafts survive offline/reload;
only connected explicit save changes server scheduling. Server actions are disabled offline,
and test sending requires saved, enabled preferences. Explain unsupported/denied permission,
Home Screen installation, setup and changed-key states. Queued/saved/pending feedback and
“Last accepted by delivery service” must not imply device receipt. Notification navigation
preserves an active recipe editor and offers a status banner whose “Open reminder” action
is disabled until editing finishes. There is no offline local notification scheduler.

See the [reminder guide](../../docs/REMINDERS.md) and fresh
[manual reminder UI finish review](../../docs/validation/reminders-review.md): **ship at the
tested reminder UI scope**, with no required UI fixes. Four genuine desktop/German dark
phone captures show connected/saved controls using synthetic household/subscription/vendor
data; the handoff banner and other states were inspected in source. This documentation
handoff did not rerun browser checks. The launcher, detector and specialist were unavailable;
no schema validation or specialist pass is claimed. Real permission prompts, live push,
Safari/physical iPhone delivery, background OS display, Focus behavior and full-product
acceptance remain outside the evidence. That historical reminder handoff preceded receipt
of the original brand artwork and introduces no replacement aesthetic direction.

Historical shared-planning handoff, 2026-10-21: Settings → Meal suggestions uses the established
solid Settings group, labelled category checkboxes and optional fixed-portions field.
Defaults are dinner, no repeats, each recipe's own servings and available leftovers enabled.
Explicit online save shares household choices. Per-device drafts persist immediately through
offline/reload, separately from the validated saved snapshot used for offline suggestions;
refreshing shared choices preserves unsaved drafts. Explain the distinction before Save.
Empty categories disable save; busy work disables the form. Success reminds users that
plans still need approval; errors explain portions/connection recovery and retained drafts.
Isolated demo settings remain local to the demo.

The multi-category preview shows weekday/category, actual recipe, portions and ranking reason
in the scrolling Sheet. Users select rows and explicitly add them to the calendar; previewing
writes no meals. Zero selection disables approval; regeneration resets selection. A synchronous
guard prevents rapid repeated activation before the first await. During the local commit,
selection/regeneration/approval/Close are disabled, the dialog exposes `aria-busy`, Escape is
blocked and the close callback guards the same-turn window. Persisted local occupancy is
reread; server approval still checks its current calendar atomically. Failure retains selection
and permits retry, with English/German guidance to check the calendar before another mix;
the copy does not promise that no write occurred after a later refresh failure. Learning counts
each distinct recipe once per successful approval, alongside the meal writes/replay receipt;
failed approvals and duplicate delivery add no learning. A bounded bonus preserves variety,
and approval never implies cooking.

See the [planning guide](../../docs/PLANNING_PREFERENCES.md) and historical
[manual shared-planning finish review](../../docs/validation/planning-preferences-review.md):
**ship at the tested shared-planning UI scope**, with rapid-activation/recovery findings
resolved and no required UI fixes remaining. Genuine [desktop settings](../../docs/screenshots/pwa-planning-settings-desktop.png),
[German dark phone settings](../../docs/screenshots/pwa-planning-settings-phone-de-dark.png)
and [offline phone preview](../../docs/screenshots/pwa-planning-preview-phone.png) captures
show the reviewed idle composition. The review records supplied real Chromium evidence of
one 21-mutation approval group after same-turn double activation and once-only server learning;
failure/dismissal branches were inspected in source. This manual documentation handoff did
not rerun browser checks or claim detector, specialist or plugin-schema validation. Full
accessibility, physical Safari/iPhone, native parity, complete-product and original-artwork
acceptance remain outside this scope. The then-reviewed glass/system-type/forest-green world is historical palette evidence; current colours follow the approved refresh below. Current supplied-artwork delivery is recorded above and in BRANDING.md.

Current palette/voice handoff, 2026-10-21: the user requested the Mealf design across every PWA and admin surface, with cheeky food innuendo and a login headliner. `frontend/src/tokens.css` owns the shared semantic palette; the build exports exact bytes to `/app/theme.css` for console reuse. `--accent*` replaces green-named roles. Preserve original PNGs byte-for-byte, system typography, solid forms, durable work and explicit import/suggestion approval. English/German welcome/login, empty-state, sidebar and footer copy may be playful. Setup instructions, help, security, error and recovery language stays literal. Current screenshots and exact light/dark tokens are in [DESIGN.md](../../DESIGN.md) and the project-owned [snapshot](../design.json); historical captures above retain their tested-source scope.

Local 213 backend/39 web tests, lint/type/contract/build checks, asset/licence checks and real Chromium PWA/admin/push-receiver flows passed in the implementation handoff. Expanded admin Axe setup/login/six-page theme checks, PWA palette pairs and narrow/enlarged-text overflow checks passed. The [manual palette finish review](../../docs/validation/mealf-palette-review.md) records **ship within the reviewed palette, administration and copy scope**, with zero required material findings. Publication remains pending and complete-product readiness is not claimed. No unavailable launcher/detector/schema pass, physical iPhone/Safari or live-service verification is claimed. Native is unchanged and retained for later.

Touch refinement, 2026-10-21: block ordinary page pinch/double-tap zoom; suppress accidental selection on app controls and labels while keeping recipe reading
content and input fields selectable. This follows the user’s confirmed clarification.
Preserve recipe copy menus, input editing and single-finger scrolling. Keep normal viewport metadata and browser/OS keyboard accessibility
zoom. The console is outside this interaction change. See PWA.md's gesture policy and
scripts/pwa_browser_smoke.py; Chromium behavior passed, physical Safari/iPhone unverified.

Peach interaction update, 2026-10-21: the original peach is now a native button with a
44px minimum hit target; wordmark navigation is a separate link. Tap, Enter or Space
starts a silent 560ms hand-swipe/squash/wobble and one of four EN/DE comebacks.
Reduced motion retains a caption and accent-soft feedback without movement. Repeated
activation cancels prior motion; hiding or resizing clears it. Shared peach.js/peach.css
ship in the PWA offline shell and admin console. Existing palette tokens and artwork
bytes are unchanged. See [behavior and scoped manual evidence](../../docs/PEACH_EGG.md).
Chromium click/keyboard/reduced-motion/offline/admin checks pass. Physical Safari/iPhone
and screen-reader delivery are unverified; no independent specialist/schema pass claimed.

Phone viewport refinement, 2026-10-21: keep mobile input/select/textarea text at least
16px and Safari text-size-adjust at 100%. Preserve ordinary viewport metadata, accessibility
zoom and user data. Layout-only --safe-top/right/bottom/left properties read the four CSS
safe-area insets. Shells, navigation and dialogs reserve those edges; short touch landscape
uses bottom navigation. No overflow hiding or viewport-reset script masks layout errors.
Chromium focus/geometry checks use injected notch values; CI also runs WebKit. Physical
iOS installation/keyboard and status-bar behavior remain outside Linux engine evidence.

Mobile calendar update, 2026-10-21: add a 44px-target segmented Day/3 days/Week choice
below the anchored week strip. Preserve readable 160px-minimum multi-day columns with
horizontal scrolling, aligned category rows and the selected day visible. Explicit
44px grips move meals using Pointer Events; card taps and ordinary scrolling retain
their roles. Show an inverse-ink drag preview, accent-soft target and faded source.
Direct manipulation has no decorative transition. Cancellation never commits; taps
and keyboard activation open the existing date/category form. Retain native desktop
drops, offline transactions and occurrence exceptions. Narrow <=480px dialogs stack
paired fields; two-column rows use minmax(0,1fr), constrained date controls and 48px
paired-field heights. Original art and palette tokens stay intact. Chromium captures/
behavior are genuine synthetic-data evidence; physical iPhone remains unverified.

Theme-library refinement, 2026-10-21: Flo preserves the current system palette. The user
requested a fixed dark-romance palette (After Dark: ink/oxblood/rose/gold) and a fixed
light palette (Sunday: linen/sage). Both use the same shared semantic tokens and original
art, with native field colour schemes. Browser-local choice covers PWA/console and
persists offline; no API/storage identity change. See docs/THEMES.md and DESIGN.md.

Personal ChatGPT text-import extension, 2026-10-22: Settings adds an optional connection
owned by the signed-in browser session. Other household members connect their own
accounts; the connection is not pooled. Preserve the established system type, shared
theme roles, solid Settings/import surfaces, glass navigation and original artwork.
Literal ordered instructions download/run a Windows-friendly Python standard-library
helper on the browser computer, then paste a private one-use pairing code and return
to choose an available model. Keep command/account wrapping, selectable code, expiry,
Copy/Cancel, reconnect/disconnect and allowance/revocation guidance understandable.

The personal import choice accepts supplied recipe text only in this first milestone.
Show the selected account/model/destination and require explicit consent to send the
text and allow this import to finish after the app closes. Bind durable queued approval
to that connection/model; preserve the existing editable preview and explicit Save.
Reviewed recipes become shared household content. Credentials remain encrypted on the
server; this UI documentation does not independently audit their handling. See the
[setup and behavior guide](../../docs/CHATGPT.md).

The [bounded finish review](../../docs/validation/chatgpt-ui-review.md) records **ship
within the reviewed UI scope**, independent persistence pass and TYPE/MATERIAL/GROUND
match, with no material UI fixes. Four genuine Chromium synthetic-household captures
show desktop pairing/connected sections, a German dark phone connected section and
the full-document German dark personal import page. Phone wrapping is an accepted
adaptation. Supplied local browser evidence passes real PWA/server/helper loopback,
signed-token verification, model choice, reviewed Save, offline replay and desktop/phone
Axe; OpenAI identity/inference and HTTPS helper-origin routing are explicit doubles.
The documentation handoff opened the captures and inspected sources, without rerunning
those checks. Launcher/detector were unavailable and no passes are claimed. Live
subscription eligibility, actual Windows execution, physical iPhone and exact-source
CI/device evidence remain unverified here. Historical design-document drift remains
preserved. This is an established task-flow extension without a new approved comp,
seed or design card, and does not declare production acceptance or a security audit.

Shopping extension, 2026-10-22: Home, Calendar and Settings open one Shopping task page
within the existing five-destination shell. Preserve original artwork, system type,
Flo/After Dark/Sunday theme roles, solid reading surfaces and glass navigation. Lead
with the current household Monday–Sunday requirements and a prominent manual Bring!
action; stack it full width on phones. Keep literal connection/queued/error/last-success
feedback, per-item states, pantry exclusions and ownership guidance. Matching manual
Bring! items stay unchanged; purchased/manually removed requirements remain suppressed
for the week. Compatibility verification requires explicit dedicated-test-list consent
and explains temporary-item changes, expiry and failure cleanup. Loading lists alone
does not enable writes. Cached offline snapshots disclose calculation time and that
recent local edits may be missing; disable the Bring! action offline or while stale.

The [bounded Shopping finish review](../../docs/validation/shopping-ui-review.md) records
**ship within the reviewed Shopping UI scope**, supplied independent persistence pass,
TYPE/MATERIAL/GROUND and thesis/story/form match, quality ceiling reached and no material
UI fixes. This documentation handoff directly inspected sources and opened all four
genuine Chromium captures: English unverified/synced desktop and German After Dark
synced/offline phone. Phone wrapping is acceptable; fixed navigation over a document
band is full-page capture behavior. Supplied browser evidence passes real PWA/server/
worker projection, explicit verification, failed then successful manual sync, manual-item
preservation, desktop/phone Axe and offline cached reload. Bring transport is synthetic;
no live Bring!, physical iPhone/Safari, exact-source CI or publication pass is claimed.
Launcher/detector were attempted but absent, with no passes claimed. This ordinary
extension preserves DESIGN.md/design.json and acknowledges historical layout/system-only
appearance drift without repairing it. It is not whole-product or security acceptance.

Recipe source-photo refinement, 2026-10-22: shared recipe thumbnails/detail frames use
the existing original peach on the semantic soft surface for absent, unavailable or
unreadable pictures. Keep the mark decorative, proportionally contained and capped at
104px; preserve recipe names and the existing compact phone rows. AI URL imports may
attach an available source picture even when extracted facts such as servings remain
incomplete. Preserve editable preview, removal/replacement, literal warnings and explicit
Save; retain original picture attribution in recipe provenance. Local cached media remains
usable offline. No invented dish image or implicit household sample is introduced.

The [bounded source-photo review](../../docs/validation/source-photos-ui-review.md)
records **ship within the reviewed photo UI scope**, supplied independent persistence
pass, TYPE/MATERIAL/GROUND and thesis/story/form match, quality ceiling reached and no
material UI fixes. This documentation handoff inspected sources/log/script and opened all
five genuine Chromium captures: missing/unreadable desktop cards, desktop detail fallback,
full-document editable import, German After Dark phone library and offline phone reload.
The phone viewport is 390×844; full-document image dimensions are 390×914. Source/AI
network outputs are explicit doubles; the picture fixture is existing illustrative
lemon-chicken artwork in a synthetic household. Supplied browser evidence passes explicit
Save/attribution, incomplete-servings review, desktop/phone Axe and cached offline reload.
The later duplicate-placeholder CSS consolidation changes no computed style/capture and
was disclosed to the independent reviewer. The shipped specialist definition was absent;
the review is a disclosed manual fallback. Launcher/detector were attempted but absent,
with no automated design/schema pass claimed. Live source/provider, physical iPhone/Safari,
exact-source CI and publication remain outside this record. Original artwork, PRODUCT.md,
DESIGN.md/design.json and native code are preserved; historical mobile-calendar/theme-library
drift is acknowledged without repair. This is an ordinary extension, not whole-product or
security acceptance, and this documentation handoff reran no tests/browser checks.
