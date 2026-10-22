# PWA UX rework: bounded finish review

Date: 2026-10-22. Disposition: **ship at the listed-fix scope**. The fresh read-only
reviewer initially inspected the whole changed PWA UI and all 15 genuine captures,
reported one P2 Shopping status finding, then confirmed its correction: **1 resolved,
0 partial, 0 unresolved**. This records that initial review and bounded correction;
it does not establish whole-product, production or security acceptance.

## Authority and documentation boundary

The user's request was to rework the whole PWA UX so everything feels neater and nicer.
The first [Direction contract](../../.impeccable/surfaces/pwa.md) governs the current
work: orderly everyday tasks within the established operating interface. [PRODUCT.md](../../PRODUCT.md),
[DESIGN.md](../../DESIGN.md) and the project-owned [design snapshot](../../.impeccable/design.json)
provide the incumbent product/visual context. The original peach and wordmark, system
type, Flo / After Dark / Sunday roles, solid reading forms and glass controls remain.
No new visual world, approved comp, concept seed or palette-token refresh is asserted.
The [screen guide](../PWA_UX.md) explains the new entry points and Settings sections.

This documentation pass used Impeccable's document reference as a source/evidence
workflow. Its DESIGN.md regeneration path was outside the authorized write boundary:
DESIGN.md and design.json were read and preserved byte-for-byte. Their historical
five-destination navigation, old layout/type/image measurements, selected-day-only
phone Calendar and system-only appearance statements are snapshot drift. The current
surface contract, runtime sources and later theme/navigation records describe the
implemented behavior; this pass does not repair or reinterpret those historical files.
The sidecar remains the project's version-1 snapshot, not a validated plugin schema.

## Reviewed implementation

Sources inspected: `frontend/src/App.tsx`, `Calendar.tsx`, `Recipes.tsx`, `Settings.tsx`,
`Imports.tsx`, `Shopping.tsx`, `Pantry.tsx`, `components.tsx`, `main.tsx` and the new
`task-layout.css`, with `scripts/pwa_ux_browser_smoke.py` and supplied evidence logs.

- Home prioritizes the selected day's meals, a compact previous/Today/next date row
  and a labelled Plan a meal action. Import, writing a recipe and inspiration follow
  the meals; the week, suggestions and recipe-book shortcuts remain available.
- Calendar groups week/date and Day / 3 days / Week controls above the board. Tools
  is labelled; suggestions, movement guidance, Shopping and leftovers follow it.
  Narrow multiple-day boards scroll internally; explicit move/copy remains available.
- Recipes puts labelled Import and New recipe actions alongside search, name/rating
  sorting and recipe ideas. Detail and editor pages gain ingredients/method anchors.
  The editor starts with name/servings, discloses optional metadata and retains fields
  while collapsed. Invalid fields reveal their containing disclosure. The sticky Save
  bar distinguishes a local draft from an explicitly saved recipe.
- Settings presents named expandable groups with short explanations. Mounted forms
  retain draft values when collapsed; connection errors reveal This device and blocked
  work opens for attention. Installation, storage and history recovery remain distinct.
- Import foregrounds URL and photo/screenshot choices while text/file and explanatory
  content use disclosures. Consent, editable review and explicit Save remain. Pantry
  foregrounds entry/availability controls and discloses its longer explanation.
- All six primary destinations remain, with compact phone branding and truthful
  connection status. Shopping retains current-week requirements and manual Bring!
  behavior. Its unconfigured state now emphasizes setup and a disabled secondary sync
  action instead of suggesting work is already being reconciled.

The visual hierarchy uses the existing semantic palette/materials, clearer labels,
compact headings, restrained groups and wrapping phone actions. The captures support
the intended task order and readable English/German adaptations at the sampled sizes.
No new stock or generated raster was introduced. Household records are synthetic;
the chicken picture is the existing original AI-generated demo illustration, explicitly
identified as such in the fixture's provenance. It is not evidence of actual cooking
or implicit sample insertion into a real household. Original artwork provenance remains
in [art](../../frontend/public/art/provenance.json) and [brand](../../frontend/public/brand/provenance.json) records.

## Finding and correction

| Finding | Final correction | Verdict |
| --- | --- | --- |
| P2: an unconfigured Bring! connection with a queued projection could say it was reconciling and visually emphasize the unavailable action. | `Shopping.tsx` requires `connection_state === 'ready'` before queued/running jobs count as progress. Unready sync is secondary and disabled; configuration is prominent where appropriate. | Resolved |

After the correction the implementation rebuilt once and recaptured the same 15 views.
The same fresh reviewer confirmed the listed fix with no partial or unresolved finding.
The supplied browser script checks the real unconfigured queued-projection presentation
and separately intercepts a response to exercise **ready + queued** progress. That
second state is an explicit UI fixture, not a live Bring! connection. The documentation
pass independently opened all final captures and inspected the readiness gate and
assertions; it did not rerun builds, tests or browser workflows.

## Final genuine capture matrix

All images below were opened directly by this documentation pass and by the fresh
reviewer. These are Chromium full-document screenshots, with animation disabled for
capture. Viewport dimensions differ from the exported document height.

| Capture | Viewport / language / appearance |
| --- | --- |
| [Home desktop](../../.impeccable/review/pwa-ux/home-desktop.png) | 1440×1000 / EN / Flo light |
| [Calendar desktop](../../.impeccable/review/pwa-ux/calendar-desktop.png) | 1440×1000 / EN / Flo light |
| [Settings desktop](../../.impeccable/review/pwa-ux/settings-desktop.png) | 1440×1000 / EN / Flo light |
| [Home phone](../../.impeccable/review/pwa-ux/home-phone-de-dark.png) | 390×844 / DE / After Dark |
| [Calendar phone](../../.impeccable/review/pwa-ux/calendar-phone-de-dark.png) | 390×844 / DE / After Dark |
| [Recipes phone](../../.impeccable/review/pwa-ux/recipes-phone-de-dark.png) | 390×844 / DE / After Dark |
| [Pantry phone](../../.impeccable/review/pwa-ux/pantry-phone-de-dark.png) | 390×844 / DE / After Dark |
| [Shopping phone](../../.impeccable/review/pwa-ux/shopping-phone-de-dark.png) | 390×844 / DE / After Dark |
| [Settings phone](../../.impeccable/review/pwa-ux/settings-phone-de-dark.png) | 390×844 / DE / After Dark |
| [Recipe detail](../../.impeccable/review/pwa-ux/recipe-detail-phone.png) | 390×844 / EN / After Dark |
| [Recipe editor](../../.impeccable/review/pwa-ux/recipe-editor-phone.png) | 390×844 / EN / After Dark |
| [Import](../../.impeccable/review/pwa-ux/import-phone.png) | 390×844 / EN / After Dark |
| [Narrow Calendar](../../.impeccable/review/pwa-ux/calendar-phone-320-de-dark.png) | 320×740 / DE / After Dark |
| [Narrow Settings](../../.impeccable/review/pwa-ux/settings-phone-320-de-dark.png) | 320×740 / DE / After Dark |
| [Narrow Home](../../.impeccable/review/pwa-ux/home-phone-320-sunday.png) | 320×740 / DE / Sunday |

Fixed navigation and the sticky Save bar retain their initial viewport bands in these
full-document exports. The underlying documents scroll; overlap in the tall exported
images is not a claim that those bands cover the same content at every scroll position.
The narrow Calendar intentionally clips adjacent columns inside its horizontal board.
Static captures do not establish motion, keyboard behavior or screen-reader delivery.

## Supplied verification and limits

`build/pwa-ux-browser.log` reports passing real FastAPI/SQLite/session navigation across
all six destinations, disclosure reveal, EN/DE, three themes, search/rating sorting,
anchors, retained optional metadata and offline recipe Save/reload/reconnect/sync.
The script audits document width and Axe WCAG 2 A/AA + 2.1 AA at desktop, 390px and
320px; the multiple-day Calendar retains internal scrolling. This is sampled automated
accessibility evidence, not complete accessibility compliance.

The supplied backend log passes **425 tests**; frontend log passes **66 tests**.
Existing `build/ux-{pwa,sync,shopping,layout,chatgpt,ai_import,source_photo,recipe_ideas,image_import,push}-regression.log`
records pass. These cover durable edits/sync/recovery, Bring projection and manual-item
preservation, mobile geometry, personal/household AI import, source pictures, recipe
ideas, local OCR and reminder receiver behavior. External Bring/provider/identity/push
responses are explicit doubles; the push receiver is injected. Browser chooser/OCR
checks do not establish physical-camera performance.

`build/ux-webkit-regression.log` records a missing local Playwright WebKit executable.
WebKit did not pass locally; the configured CI run is pending at this handoff. The
context launcher was known absent and the detector was attempted but unavailable;
source/capture inspection is the disclosed fallback. No automated detector, plugin
schema, design-hook or unavailable shipped specialist-definition pass is claimed.

Canonical API/sync schema and the independent native pin are intentionally unchanged.
Live Bring!, AI and Web Push, physical iPhone/Safari, installed-PWA keyboard/VoiceOver,
the user's actual deployment and exact-source CI/publication remain unverified here.
The documentation pass reran no tests or browser checks. The bounded verdict does not
diagnose the user's earlier deployment/sync issue or certify every feature/state.
