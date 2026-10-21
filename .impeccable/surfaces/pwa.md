# mealf PWA operating surface

Mode: Operate. Approved purpose/platform: PWA-first, retaining native code; user confirmation
on 2026-10-21. Preserve the approved native concept and product requirements. Stack choice
is delegated by the master prompt. The confirmed mealf name/asset rebrand applies to the
established glass interface; it does not replace that approved visual world.

Visual authority: existing SwiftUI KitchenStyle/components and the user-approved glass
concept at /workspace/generated_images/exec-d61616a4-31c5-4cbf-8f34-24d3ed52d35f.png.
The image is labelled illustrative; it is not a product capture. Supporting private design
references apply to the conversation only; preserve the approved decisions, not private IDs.

First viewport: Your kitchen heading and compact import/create actions, household civil-week
strip, today's actual meals with one strong food photo when present, accessible empty-slot
actions and visible offline/demo status. Bottom glass five-destination navigation on phones;
adapt content density and navigation on desktop. Existing account data never gains samples.

Restrained colour: system-like white/charcoal content, forest-green actions, warm food
photography. Follow system appearance. System UI typography is intentional continuity with
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

Brand delivery, 2026-10-21: display names now use mealf. The supplied flirty peach icon
(`mealf-flirty-peach-logo.png`) and lowercase wordmark (`mealf-flirty-peach-wortmarke.png`)
are visible only as conversation previews; exact source PNGs are not mounted or downloadable.
Install the supplied originals exactly once available, without recreating them. The old
generated icons, crossed-utensil marks and plain mealf text remain interim treatments.
Artwork installation and the complete branding request remain blocked and incomplete.
See [branding](../../docs/BRANDING.md) and the newest
[name-only review](../../docs/validation/mealf-name-review.md): ship at name-only scope,
with no original-artwork or complete-product acceptance. Historical PWA reviews/captures
retain their original scope. This manual handoff claims no launcher/detector, schema,
design-hook or specialist pass.

Reminder handoff, 2026-10-21: Settings includes optional per-device meal reminders within
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
acceptance remain outside the evidence. Exact peach/wordmark artwork remains blocked as
recorded above; this handoff introduces no new aesthetic direction or replacement artwork.

Shared-planning handoff, 2026-10-21: Settings → Meal suggestions uses the established
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

See the [planning guide](../../docs/PLANNING_PREFERENCES.md) and newest
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
acceptance remain outside this scope. Preserve the approved glass/system-type/forest-green
world and the exact-original-PNG artwork blocker above.
