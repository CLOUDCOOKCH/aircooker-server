---
name: mealf web
description: Food-led household planning and administration with system type and glass navigation.
colors:
  canvas: "#fff7ec"
  surface: "#fffdf8"
  ink: "#32221f"
  muted: "#79635b"
  line: "#dfc8bb"
  soft: "#f6e9dc"
  hover: "#efdbcd"
  accent: "#a83b2b"
  accent-hover: "#943323"
  on-accent: "#ffffff"
  accent-soft: "#f9e1d7"
  accent-ink: "#813426"
  accent-muted: "#7c5147"
  focus: "#a83b2b"
  selection: "#f2b49c"
  glass: "rgba(255, 247, 236, 0.84)"
  scrim: "rgba(43, 24, 19, 0.44)"
  control-border: "#a88b7e"
  danger: "#a12340"
  danger-soft: "#fbe4e9"
  danger-ink: "#851e36"
  warning-soft: "#f6e8c8"
  warning-ink: "#6d4b16"
  canvas-dark: "#201917"
  surface-dark: "#2c2220"
  ink-dark: "#fff2e8"
  muted-dark: "#c8aaa0"
  line-dark: "#54403a"
  soft-dark: "#392b27"
  hover-dark: "#49342e"
  accent-dark: "#ffad8c"
  accent-hover-dark: "#ffc6af"
  on-accent-dark: "#3a211a"
  accent-soft-dark: "#493029"
  accent-ink-dark: "#ffd6c2"
  accent-muted-dark: "#dcb4a2"
  focus-dark: "#ffad8c"
  selection-dark: "#754b3b"
  glass-dark: "rgba(44, 34, 30, 0.86)"
  scrim-dark: "rgba(12, 7, 5, 0.64)"
  control-border-dark: "#a48679"
  danger-dark: "#ffa6ba"
  danger-soft-dark: "#48232e"
  danger-ink-dark: "#ffc8d4"
  warning-soft-dark: "#42321e"
  warning-ink-dark: "#f0d49f"
typography:
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "2.375rem"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.035em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: "1rem"
    lineHeight: 1.6
rounded:
  input: "11px"
  button: "12px"
  surface: "16px"
  sheet: "20px"
  desktop-nav: "24px"
  phone-nav: "27px"
---

# mealf web design reference

2026-10-22 error-recovery refinement: Recipe ideas uses existing alert/action styles for
specific localized provider failures, allowlisted diagnostic codes and a Settings route.
PWA/admin model-ID help preserves the existing fields and visual system. See the bounded
[manual source/capture review](docs/validation/recipe-ideas-errors.md); this is not live
Gemini or physical-iPhone acceptance and does not regenerate this historical snapshot.

This is the implementation snapshot for the PWA `frontend/` and administration console, dated 2026-10-21. The direction contract is [PRODUCT.md](PRODUCT.md) and the existing [PWA surface brief](.impeccable/surfaces/pwa.md). The independent native iOS app is retained for later. This document records the approved effortless, food-led, cream/coral/peach and cocoa/peach, system-type, iOS-like glass direction; it does not reopen design selection or replace the master product requirements. Surface mode remains recorded only in the surface brief.

## Overview

The user explicitly requested the Mealf palette and cheeky food voice across the whole PWA and console. This approval supersedes the earlier forest-green constraint while preserving glass navigation, solid reading/editing surfaces, system type and the supplied original PNGs. Native implementation remains unchanged. See both the [PWA](.impeccable/surfaces/pwa.md) and [admin](.impeccable/surfaces/admin.md) surface briefs.

### Authority and historical evidence

The user-approved glass concept supplied in the conversation is illustrative, not a running app capture. It and the established native KitchenStyle/components inform the visual continuity recorded here. The concept image is not a published repository artifact.

The historical [finish review](docs/validation/pwa-visual-review.md) and [fix verdict](docs/validation/pwa-visual-verdict.md) record the original PWA acceptance scope. Their verdict is **ship within the reviewed screenshot/source and two-fix scope**, with 2 resolved, 0 partial and 0 unresolved findings. It does not declare the complete product ready. The final matrix is seven genuine captures: [welcome desktop](docs/screenshots/pwa-welcome-desktop.png), [Home desktop](docs/screenshots/pwa-home-desktop.png), [Home phone light](docs/screenshots/pwa-home-phone.png), [Home phone dark](docs/screenshots/pwa-home-phone-dark.png), [Recipes phone dark](docs/screenshots/pwa-recipes-phone-dark.png), [German Settings phone dark](docs/screenshots/pwa-settings-phone-de-dark.png) and [German Calendar phone dark](docs/screenshots/pwa-calendar-phone-de-dark.png). Desktop viewport was 1440×1000 and phone viewport 390×844; full-document images retain fixed navigation at the original viewport position. Captures do not establish motion quality.

The [mealf name-only finish review](docs/validation/mealf-name-review.md), dated 2026-10-21, records **ship the reviewed name-only change**, with no blocking finding at that scope. It reviews the working-tree name changes and five genuine captures in `.impeccable/review/mealf-name/`; it does not accept the original artwork delivery or a complete rebrand. The historical reviews, capture matrix and screenshot hashes remain records of their original tested sources.

The [manual reminder UI finish review](docs/validation/reminders-review.md), dated 2026-10-21, records **ship at the tested reminder UI scope**, with no required UI fixes. It covers reminder settings and the notification handoff banner through source inspection and four genuine desktop/German dark phone captures of synthetic household/subscription/transport data. The captures show connected/saved controls; the editor-preserving banner was reviewed in source. Other error/offline/busy states were inspected in source, not all captured. See the [reminder guide](docs/REMINDERS.md) for behavior and delivery limits.

The historical [manual shared-planning finish review](docs/validation/planning-preferences-review.md), dated 2026-10-21, records **ship at the tested shared-planning UI scope**. Its bounded confirmation resolves rapid repeated approval and recovery wording, with no required UI fixes remaining. Three genuine captures show [saved settings on desktop](docs/screenshots/pwa-planning-settings-desktop.png), [German dark phone settings](docs/screenshots/pwa-planning-settings-phone-de-dark.png) and an [offline multi-category phone preview](docs/screenshots/pwa-planning-preview-phone.png). Settings captures are full-document images at 1440×1000/390×844 viewports; the preview scrolls within its dialog. Idle capture hashes remained unchanged by the pending/error fix. The review records a supplied real Chromium same-turn double-activation run checking one 21-mutation approval group and once-only server learning; failure/dismissal branches were reviewed in source. See the [planning guide](docs/PLANNING_PREFERENCES.md) for shared defaults, offline drafts and learning limits. This documentation handoff inspected those records and current sources; it did not rerun browser checks. The context launcher, detector, cloud resources and specialist definition were unavailable. No specialist pass is claimed.

[design.json](.impeccable/design.json) uses **mealf's project-owned snapshot schema, version 1**, retaining the compatibility ID `mealf.design-snapshot`. Its `tokens.cssCustomProperties` contains exact CSS strings, and its other token groups record literal implementation measurements. It is a documentation snapshot, not a runtime token source. The plugin schema, cloud design resources and shipped documentation specialist definition were unavailable. No plugin schema validation, automated design detector or design-hook pass is claimed. No generation prompt has been reconstructed.

### Current palette evidence and limits

Local verification reported by the implementation handoff passed 213 backend tests and 39 web core tests, Ruff lint/format, mypy, OpenAPI drift, frontend build/type checks, original/derived asset integrity and the licence inventory. Real Chromium PWA, console and push-receiver workflows passed using synthetic external-service data. Expanded admin Axe checks cover setup/login and all six pages in both themes; PWA palette-pair checks and 320px/200% text overflow checks also passed. This documentation handoff extracts sources and preserves genuine captures; it does not independently rerun those checks.

Current genuine renders are linked below. These captures depict synthetic household/demo data, never an implicitly populated existing household. Static images do not establish motion, screen-reader or physical-device behavior. The [manual palette finish review](docs/validation/mealf-palette-review.md) records **ship within the reviewed palette, administration and copy scope**, with zero required material findings after source inspection and all 12 required captures. Publication is pending; this bounded verdict does not establish complete-product readiness. Launcher/detector and plugin-schema passes are unavailable. Live Web Push, Bring!, AI and physical iPhone/Safari remain unverified. Earlier published preview/CI evidence does not certify this newer source tree.

- PWA: [welcome desktop](docs/screenshots/mealf-palette-pwa-welcome-desktop.png), [welcome dark phone](docs/screenshots/mealf-palette-pwa-welcome-phone-dark.png), [login desktop](docs/screenshots/mealf-palette-pwa-login-desktop.png), [Home desktop](docs/screenshots/mealf-palette-pwa-home-desktop.png), [Home dark phone](docs/screenshots/mealf-palette-pwa-home-phone-dark.png), [Recipes dark phone](docs/screenshots/mealf-palette-pwa-recipes-phone-dark.png), [German dark Settings](docs/screenshots/mealf-palette-pwa-settings-phone-de-dark.png).
- Admin: [login desktop](docs/screenshots/mealf-palette-admin-login-desktop.png), [German dark login phone](docs/screenshots/mealf-palette-admin-login-phone-de-dark.png), [overview desktop](docs/screenshots/mealf-palette-admin-desktop.png) and [overview dark desktop](docs/screenshots/mealf-palette-admin-desktop-dark.png) and [German phone household settings](docs/screenshots/mealf-palette-admin-mobile-settings-de.png).

### Visual language and content

Use warm food imagery against cream or cocoa surfaces, with coral/peach accent roles for primary actions and selection. Raspberry danger roles remain distinct from the food accent. Localized food innuendo belongs in welcome/login, empty-state, sidebar and footer copy; setup/help, security, errors, recovery and action labels stay literal. Keep reading and editing surfaces solid and legible. Reserve glass for floating navigation; modal backdrops may blur the surrounding scene. Do not add a marketing hero, invented metrics, ornamental dashboards, emoji icons, gradient type or decorative eyebrow headings to the operating UI. Preserve the approved food/card treatment.

The first kitchen view combines the heading and compact create/import controls, civil-week strip, actual selected-day meals, useful empty-slot actions and visible demo/offline status. Selecting a day updates its meal composition while the week/navigation stay anchored. Preserve five destinations: Home, Calendar, Recipes, Pantry and Settings. Import and suggestion flows require review before explicit apply/save; local work and recovery state must remain understandable. Existing households never gain implicit sample recipes or meals.

## Colors

Source of truth: [tokens.css](frontend/src/tokens.css). The build copies these exact bytes into `/app/theme.css`, imported by the administration console; its `--bg`, `--fg`, `--panel`, `--border` and `--active` aliases map to canvas, ink, surface, line and accent-soft. Do not maintain a separate admin palette. Dark values follow `prefers-color-scheme: dark`; `html` declares `color-scheme: light dark`. Change foreground/background pairs together rather than fading between themes.

| CSS token | Light | Dark | Role |
| --- | --- | --- | --- |
| `--canvas` | `#fff7ec` | `#201917` | Page background |
| `--surface` | `#fffdf8` | `#2c2220` | Solid reading/editor/card surface |
| `--ink` | `#32221f` | `#fff2e8` | Primary text |
| `--muted` | `#79635b` | `#c8aaa0` | Supporting copy/placeholders |
| `--line` | `#dfc8bb` | `#54403a` | Dividers |
| `--soft` | `#f6e9dc` | `#392b27` | Secondary controls/search |
| `--hover` | `#efdbcd` | `#49342e` | Neutral hover |
| `--accent` | `#a83b2b` | `#ffad8c` | Primary action/active icon |
| `--accent-hover` | `#943323` | `#ffc6af` | Primary hover |
| `--on-accent` | `#ffffff` | `#3a211a` | Primary action/selected-day text |
| `--accent-soft` | `#f9e1d7` | `#493029` | Selection/suggestion background |
| `--accent-ink` | `#813426` | `#ffd6c2` | Information heading |
| `--accent-muted` | `#7c5147` | `#dcb4a2` | Information supporting copy |
| `--focus` | `#a83b2b` | `#ffad8c` | Focus outline |
| `--selection` | `#f2b49c` | `#754b3b` | Text selection |
| `--glass` | `rgba(255, 247, 236, 0.84)` | `rgba(44, 34, 30, 0.86)` | Floating navigation |
| `--scrim` | `rgba(43, 24, 19, 0.44)` | `rgba(12, 7, 5, 0.64)` | Modal backdrop |
| `--control-border` | `#a88b7e` | `#a48679` | Field/secondary control outline |
| `--danger` | `#a12340` | `#ffa6ba` | Destructive action |
| `--danger-soft` | `#fbe4e9` | `#48232e` | Error background |
| `--danger-ink` | `#851e36` | `#ffc8d4` | Error copy |
| `--warning-soft` | `#f6e8c8` | `#42321e` | Sync/update banner background |
| `--warning-ink` | `#6d4b16` | `#f0d49f` | Sync/update banner copy |

## Typography

Source: [styles.css](frontend/src/styles.css:5). Use `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`; the system stack is intentional, with no required web font. Root size is 16px; controls inherit typography. Preserve scalable rem-based text and wrapping. Imported recipe text retains its original language; interface copy supports English/German and count-sensitive serving labels.

| Role | Size | Weight | Line-height / tracking |
| --- | --- | --- | --- |
| Desktop h1 | `2.375rem` | 700 | `1.15 / -0.035em`, balanced wrapping |
| h1 at ≤800px | `2rem` | 700 | Inherits h1 line-height/tracking |
| h2 | `1.25rem` | 650 | `1.3 / -0.02em` |
| h3 | `1rem` | 600 | `1.35` |
| Body paragraph | Inherited `1rem` | Normal | `1.6` |
| Button/field label | `0.875rem` | 600 / 550 | Inherits where unspecified |
| Supporting text | Commonly `0.75–0.95rem` | Contextual | Usually `1.4–1.7` |
| Welcome h1 | `2.75rem`, ≤800px `2.5rem`, ≤600px `2.375rem` | 700 | `1.12 / -0.035em` |

## Layout

Source: [styles.css media rules](frontend/src/styles.css:1629). Breakpoints are CSS viewport pixels, inclusive as written; smaller maximum-width rules override earlier rules.

| Rule | Implemented adaptation |
| --- | --- |
| Base desktop | App max 1660px; page max 1160px. Fixed sidebar width 196px, 24px outer inset; main margin-left 252px with 40px horizontal padding. Home columns `1.5fr / minmax(260px, 1fr)`, gap 36px; recipe grid 3 columns. |
| ≥1550px | Main horizontal padding 55px; Home gap 44px; featured image 360px high. |
| ≤1180px | Sidebar 172px, 18px inset; main margin-left 204px, horizontal padding 24px. Home `1.3fr / minmax(220px, 1fr)`, gap 24px. Recipes 2 columns; recipe previews one column; featured image 260px. Pantry rows wrap. |
| ≤800px | Sidebar becomes bottom nav: width `min(520px, calc(100vw - 32px))`; bottom `max(16px, env(safe-area-inset-bottom))`; 5 horizontal labelled controls, minimum 55px height. Brand/household sidebar footer hidden. Main margin 0 and padding `10px 24px 100px`. H1 2rem. Home remains two columns until 600px; featured image 250px. Toast centered at bottom 100px. |
| ≤600px | Main padding `8px 20px 108px`. Home, recipe detail, Settings and Imports become single column; Home gap 28px. Recipes become divided rows with 84×84px thumbnails. Calendar shows selected day only, with full-width meal rows. Header actions collapse to 44px icons with accessible names. Featured image 235px; detail image 245px. Banner/actions wrap and editor save spans width. |

Base featured image height is 310px; base detail image 380px (320px at ≤800px). Calendar uses seven horizontally scrollable columns, minimum 165px each; at ≤800px minimum is 180px, before the ≤600px selected-day layout. Sheets are `min(540px, calc(100vw - 24px))` wide, max-height `calc(100dvh - 48px)` or phone `calc(100dvh - 32px)`, with internal overflow. Respect bottom safe areas and reserved content padding; do not use full-document capture position alone to diagnose fixed navigation.

## Elevation & Depth

Glass remains structural navigation material; solid content panels protect reading contrast.

| Elevation | Light | Dark |
| --- | --- | --- |
| `--glass-shadow` | `0 8px 32px rgba(83, 42, 25, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.8)` | `0 10px 36px rgba(0, 0, 0, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.08)` |
| `--sheet-shadow` | `0 18px 70px rgba(55, 28, 20, 0.22)` | `0 22px 80px rgba(0, 0, 0, 0.5)` |

Navigation uses `blur(28px) saturate(155%)`, z-index 10. Sheets use a `var(--scrim)` backdrop with `blur(5px)`. Toasts use the glass shadow, inverse ink/canvas colours and z-index 30; the focus-only skip link uses z-index 100. Do not treat translucency as a substitute for contrast testing on actual composited backgrounds.

## Shapes

Use section space larger than within-group space: section blocks 36px; heading-to-content commonly 16–24px; compact related controls 8–14px. These are observed CSS measurements, not a newly imposed universal scale. Common layout gaps are 20, 24, 28, 30, 36 and 44px. Preserve component-specific values instead of rounding every measurement to an invented grid.

| Shape/measurement | Implemented value |
| --- | --- |
| Inputs | 11px radius; 12px 13px padding; minimum 46px height |
| Primary/secondary buttons | 12px radius; 12px 20px padding; minimum 46px height; 9px icon gap |
| IconButton default | 44×44px, circular; smaller local overrides exist |
| Solid content cards/groups | Usually 16px radius |
| Week day / calendar card | 14px radius |
| Sheet | 20px radius; 24px padding, phone 20px |
| Desktop nav / phone nav | 24px / 27px radius |
| Recipe preview/thumb | 12px radius; meal thumb 10px |
| Toast | 30px radius |

Do not infer a universal 44px target guarantee: slot, calendar and editor controls have smaller overrides. Retain explicit labels and assess target size and text enlargement in future acceptance work.

## Components

Source: [components.tsx](frontend/src/components.tsx), [App.tsx](frontend/src/App.tsx), [Calendar.tsx](frontend/src/Calendar.tsx), [Recipes.tsx](frontend/src/Recipes.tsx), [Imports.tsx](frontend/src/Imports.tsx), [Pantry.tsx](frontend/src/Pantry.tsx), [Settings.tsx](frontend/src/Settings.tsx), [ReminderSettings.tsx](frontend/src/ReminderSettings.tsx) and [PlanningSettings.tsx](frontend/src/PlanningSettings.tsx).

- **PageHeader:** one h1, optional subtitle/back action and compact create/import actions. Preserve a clear h1/body hierarchy without decorative headings.
- **Navigation:** Lucide stroke icons with text; active destination uses `aria-current="page"`, accent-soft background and accent foreground. App uses icon size 22px, stroke 2 active / 1.6 inactive. Keep five destinations across layouts.
- **WeekStrip:** seven civil dates, named previous/next-week controls, complete spoken date labels and `aria-pressed` selected state. Selected day uses accent/on-accent and a visible dot, with tabular day numerals.
- **Meals/recipes:** use actual household records. Strong featured food imagery when present, image placeholders when unavailable, divided supporting meal rows and clear empty-slot actions. Recipe cards adapt to compact rows on phones.
- **Forms:** visible labels, muted helper text, solid field surfaces, visible focus and explicit save/apply/cancel controls. Preserve line breaks and long imported text using wrapping. Keep import preview and save separate. Preserve drafts/outbox and avoid updating the app while an editor is active.
- **Sheet:** native modal dialog with unique React `useId` heading reference through `aria-labelledby`, visible close control, native modal behavior, Escape routed through onClose and cleanup focus restoration to the opener. Planning and confirmation flows share this primitive. Optional busy state exposes `aria-busy`, disables Close and blocks Escape dismissal during the local approval commit; the approval's guarded close callback also covers the same-turn window before rendering.
- **Weekly templates:** the editor reuses Sheet and solid labelled form controls. Group each meal in a fieldset with a numbered legend; use two bounded columns for weekday/category, a full-width recipe selector and explicit portions/remove controls. Save edits separately from applying the template to a calendar week. Wrap the saved-template actions when long names or narrow widths require it.
- **Shared suggestion settings:** use the existing solid Settings group, labelled category checkboxes and optional fixed-portions field. Default to dinner, no repeats, each recipe's own servings and available leftovers enabled. Saving online shares the household choices; immediate per-device drafts survive offline/reload separately from the validated saved snapshot. Offline suggestions use that last saved snapshot, and refreshing shared choices preserves an unsaved draft. Explain this distinction before the explicit save action. Empty categories disable save; busy work disables the form. Success uses `role="status"` and reminds users that plans still require approval; an alert explains portions/connection recovery and retained drafts. Isolated demo choices stay in the demo. See the [guide](docs/PLANNING_PREFERENCES.md).
- **Suggestion preview and approval:** rows show weekday, category, actual recipe title, portions and ranking reason within the scrolling Sheet. Checked rows support exclusion; zero selection disables “Add to calendar” / “In den Kalender übernehmen”, and regeneration resets the selection. Preview generation writes no meals. A synchronous guard prevents same-turn repeated approval; selection, regeneration, approval and dismissal remain disabled during the local commit. Reread persisted local meal occupancy before saving; server approval remains atomic against its current calendar. Failure retains selection and releases the guard for retry. The alert says “Could not finish adding this preview. Check your calendar before trying another mix.” and has equivalent German guidance; do not promise that nothing was written after a later refresh failure. Each successful approval learns each distinct selected recipe once, transactionally with the meal writes and replay receipt; duplicate replay and failed approvals add no learning. Its bounded ranking bonus preserves variety, and a prior choice never implies cooking. The [fresh review](docs/validation/planning-preferences-review.md) records the bounded guard/copy confirmation and its evidence limits.
- **Meal reminders:** keep this optional, per-device section within the solid Settings surface, using the existing system typography and semantic accent controls. Show the household time zone, explicit notification connection, enable checkbox, category checkboxes with distinctly named native time inputs, and separate save/test/retry/disconnect actions. A disabled category disables its time input; busy work disables the form. Explain installation, unsupported/denied permission, setup, offline and changed-key states. Persist preference edits immediately as local drafts through offline/reload; only explicit connected save applies them to server scheduling. Disable server actions offline and test sending while edits are unsaved or reminders are disabled. Distinguish queued/saved/pending status from errors, and label timestamps “Last accepted by delivery service”; this is not proof of device display. The [guide](docs/REMINDERS.md) records best-effort delivery and the absence of an offline local scheduler.
- **Reminder navigation:** a valid notification target opens the matching calendar day or Settings. If a recipe editor is active, preserve the edit and show a status banner explaining the handoff; “Open reminder” stays disabled until editing finishes. Do not replace active work on notification arrival. The fresh [review](docs/validation/reminders-review.md) assesses this banner in source, with no screenshot or physical-device acceptance claim.
- **Loading:** boot icon/loading line plus text; content skeleton uses soft blocks. Loading line animation is 1.5s ease-out infinite. Do not substitute fabricated household records for loading/empty states.
- **Offline/sync/recovery:** connection bar shows offline, syncing, pending count or synced state plus sync action. Error/blocked sync has a `role="alert"` banner linking to Settings; preserve rejected-copy/conflict/recovery actions and durable unsynchronised work. Updates are announced with an explicit apply action; editing disables that action.
- **Feedback:** errors use danger-soft/danger-ink; warnings use warning-soft/warning-ink; notices use a `role="status"` toast. Disabled buttons use opacity 0.45 and default cursor. Disabled, loading and empty states should explain the next useful action in interface copy.
- **Demo:** explicitly entered, isolated and visibly labelled, with an exit control. Never silently add illustrated samples to connected account data.

### PWA gesture and selection policy

The user's 2026-10-21 interaction request blocks ordinary page-zoom gestures and explicitly
keeps recipes and inputs selectable while disabling accidental control selection. `html`, `body` and `#root` use `touch-action: pan-x pan-y`;
root `user-select: none` and `-webkit-user-select: none` suppress app-label selection. The recipe detail `.recipe-content` group, text inputs, textareas and editable fields opt into `text`; buttons, navigation links, labels, summaries and selects remain `none`. Source links inside recipes also opt in. `main.tsx` cancels
Safari gesture events and Ctrl+wheel pinch, but never single-finger touch events or keyboard
zoom commands. The original viewport metadata remains unchanged. Browser/OS accessibility
zoom can override page policy. Console gestures and all visual tokens remain unchanged.
Chromium touch/selection regression checks passed; physical iPhone/Safari is unverified.

## Accessibility and motion guidance

The implementation includes a focus-only skip link, named icon buttons, native field controls, visible `3px solid var(--focus)` outlines with 4px offset, selected-day semantics and named modal headings. Preserve those relationships when extracting components. Decorative cooking-pot placeholders are hidden from assistive technology; `Photo` accepts alternative text, defaults to empty text and lazily loads local/cached media. Choose useful alt text when an image carries information beyond adjacent copy.

Historical forest-green palette evidence in the original finish review (not evidence for the current palette): light muted/canvas 5.04:1, light search placeholder/soft 4.66:1, light suggestion copy 5.14:1; dark muted/surface 6.67:1, dark search placeholder 5.70:1, dark suggestion copy 6.23:1; primary text 8.78:1 light and 8.10:1 dark. This is a representative pair check, not measurement of every runtime combination. Continue to require body/placeholder contrast ≥4.5:1 and large text ≥3:1.

Button theme changes intentionally have no transition. Icon/card background hover uses 180ms ease-out; selected-day emphasis uses 180ms `cubic-bezier(0.16, 1, 0.3, 1)` from scale 0.94/blur 0.3px to scale 1/blur 0. Reduced-motion CSS disables animation/transitions and smooth scrolling. Reduced transparency makes nav opaque and removes its blur; it also removes the standard sheet backdrop blur. Unsupported backdrop-filter makes navigation opaque. Preserve the fallbacks and test actual browser behavior rather than claiming static captures prove it. Provide explicit move/copy actions alongside any drag interaction.

The published review records report passing Chromium functional smoke and captured-screen Axe WCAG 2 A/AA + 2.1 AA evidence. The exact-name “Plan a meal” browser assertion also checks modal closing and focus return ([smoke script](scripts/pwa_browser_smoke.py:257)). This documentation handoff inspected sources and review records; it did not rerun those browser checks. Complete keyboard, text enlargement, screen-reader, all-state contrast and physical iPhone/WebKit acceptance remain outside this finish evidence.

### Assets and provenance

Current artwork delivery: both original PNGs are now available and installed in the PWA
and console. See the [manual artwork review](docs/validation/mealf-artwork-review.md) and
[source/derivative hashes](docs/validation/mealf-artwork-local.json). This review is by the
implementation agent; unavailable launcher/detector/specialist passes are not claimed.
Original bytes live in `assets/brand/originals/`. Shared `Brand` markup uses a 32px peach,
8px gap and 104px-wide image wordmark; compact footer variants use 20px/6px/60px. Header
links have a minimum 44px height. System typography and the glass vocabulary are preserved. The current palette refresh changes semantic accent and neutral colours across both web surfaces; the artwork pixels remain intact.

See [provenance.json](frontend/public/art/provenance.json). `lemon-chicken.png` remains original AI-generated project illustration reused from `mealf-ios/App/Assets/DemoChicken.png`, source commit `f165c362106955db4405b5c4ce9b3fb25fbc3fd9`, generation `exec-b3e6fb11-5c8c-4b69-ae40-eb5dda3a6c00`. It is for the isolated demo only, not a real cooking photograph. Its original prompt remains unavailable. PWA icons now derive from the user-supplied peach; [brand provenance](frontend/public/brand/provenance.json) records the originals and every output. Household recipe media remains separate.

The confirmed name is **mealf**; see [branding and compatibility](docs/BRANDING.md). The original `mealf-flirty-peach-logo.png` and `mealf-flirty-peach-wortmarke.png` are installed without redrawing, tracing or recolouring. Only transparent margins, output sizes and install canvases change in derivatives. The old generated PWA icon and utensil/text lockups are replaced. Retained native artwork is separate later work. Historical name-only captures/reviews still describe their original scope, not this new artwork delivery.

### Delivery limits

This is a bounded visual/source documentation handoff. It does not establish complete original-master acceptance, physical iPhone/WebKit behavior, full native feature parity, complete accessibility compliance, live Web Push delivery, passkeys, QR UI, live Bring! or live AI verification. Reminder browser evidence uses explicit subscription/vendor doubles and a CDP-injected receiver event; real permission prompts, Safari delivery, background OS display and Focus behavior remain unverified. The PWA requires HTTPS, initial offline download/storage handling and reopening for automatic sync; native widgets remain deferred and incoming sharing uses paste/import or documented optional Shortcuts. Product and implementation records own functional status. This reference must not turn source presence or scoped review evidence into service/platform acceptance.

## Do's and Don'ts

- Do use the shared semantic accent roles and paired light/dark colours for both web surfaces.
- Do preserve the original peach and wordmark bytes, solid forms, system typography and explicit review/apply flows.
- Do keep food jokes in the approved welcome/login, empty-state, sidebar and footer contexts.
- Do retain literal setup, help, security, error and recovery language.
- Don't reuse historical green-palette contrast ratios as evidence for the current colours.
- Don't infer physical iPhone, live-service, complete accessibility or complete-product acceptance from Chromium screenshots.
- Don't rename persistent storage, session, API, archive or ownership identifiers as part of a visual change.

Peach interaction update, 2026-10-21: the original peach is now a native button with a
44px minimum hit target; wordmark navigation is a separate link. Tap, Enter or Space
starts a silent 560ms hand-swipe/squash/wobble and one of four EN/DE comebacks.
Reduced motion retains a caption and accent-soft feedback without movement. Repeated
activation cancels prior motion; hiding or resizing clears it. Shared peach.js/peach.css
ship in the PWA offline shell and admin console. Existing palette tokens and artwork
bytes are unchanged. See [behavior and scoped manual evidence](docs/PEACH_EGG.md).
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


Theme library update, 2026-10-21: the user named the established appearance **Flo** and
requested additional dark romance and light themes. Flo retains the exact approved
system palettes above. **After Dark** uses ink/oxblood/rose, dark elevation and restrained
gold details; **Sunday** uses linen whites/sage. Shared semantic roles, system type,
solid forms, glass navigation and original art remain authoritative. Explicit choices
override system media queries and set native field colour scheme. Settings provides
native radio previews; the console header provides a select. Device-local persistence,
metadata, offline shell and accessibility checks are described in [THEMES.md](docs/THEMES.md).
This extends appearance selection; historical system-only notes above describe Flo.

Theme validation follow-up: filled destructive buttons now use `--on-danger`, preserving
4.5:1 contrast with pale dark-mode danger backgrounds. At narrow phone widths, German
Settings navigation displays “Optionen” with the full “Einstellungen” accessible name.
Equal-width navigation items shrink and connection/demo controls wrap to stay inside the
viewport. The existing native fieldset/grid minima are bounded; no root overflow hiding
is used to mask layout faults.

Photo import extension, 2026-10-21: extend the existing import surface with a native
Link or text / Photo or screenshot choice and Take photo / Choose image actions. Use
shared theme roles and solid controls, a contained image preview, visible queue status
and the existing recipe editor. Review notices explain uncertainty without jokes;
recognised source text stays selectable. Existing Flo/After Dark/Sunday palettes, PNG
brand artwork, glass navigation and mobile safe-area/field constraints remain authoritative.
This is an ordinary task-flow extension, not a new visual world. Browser captures use
synthetic printed recipes; camera hardware is outside that evidence.
