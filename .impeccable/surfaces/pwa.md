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

Touch refinement, 2026-10-21: block ordinary page pinch/double-tap zoom; keep text selection,
copy menus, input editing and single-finger scrolling enabled. The request says “activate
text selector”; no reply to the optional clarification had arrived, so this follows that
literal instruction. Keep normal viewport metadata and browser/OS keyboard accessibility
zoom. The console is outside this interaction change. See PWA.md's gesture policy and
scripts/pwa_browser_smoke.py; Chromium behavior passed, physical Safari/iPhone unverified.
