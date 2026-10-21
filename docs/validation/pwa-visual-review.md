## Disposition

**Fix — one bounded accessibility correction.** The captured visual design is ready within this review's scope. Preserve the current food imagery, forest-green palette, system typography, content hierarchy, adaptive sidebar/bottom navigation and restrained glass. No redesign or new visual variant is warranted. The shared sheet needs an accessible dialog name before this finish handoff closes.

## Evidence

Independently opened the approved illustrative concept and all seven genuine round-2 captures: welcome desktop; Home desktop; Home phone light and dark; Recipes phone dark; German Settings phone dark; German Calendar phone dark. Read PRODUCT.md, .impeccable/surfaces/pwa.md, App.tsx, components.tsx, the captured feature render paths, supporting Imports/Pantry render paths, tokens.css and styles.css.

The captures show clear h1/body hierarchy, useful separation between sections, readable solid content surfaces, consistent stroke icons, a prominent original food image, explicit isolated-demo disclosure, five destinations and legible German wrapping. The desktop layout uses available width effectively. Mobile content continues below the viewport; the fixed navigation appearing over content at its original viewport position in full-document screenshots is expected capture behavior, not evidence of permanently inaccessible content.

Manual token contrast calculations support the craft floor for the inspected text pairs: light muted text on canvas 5.04:1; light search placeholder on soft surface 4.66:1; light suggestion copy 5.14:1; dark muted text on surface 6.67:1; dark search placeholder 5.70:1; dark suggestion copy 6.23:1. Primary button text is 8.78:1 light and 8.10:1 dark. Source supplies visible focus styling, named icon buttons, selected-day state, modal focus restoration, reduced-motion rules and opaque navigation fallbacks. This is a representative pair check, not a claim that every runtime combination was measured.

## Findings

- **Medium — shared modal lacks an accessible name.** Source: frontend/src/components.tsx:183. `Sheet` renders a native `<dialog>` and a visible `<h2>`, but the dialog has neither `aria-labelledby` pointing to that heading nor `aria-label`. A descendant heading does not automatically name a dialog. All planning, meal-management and confirmation sheets inherit this gap. The captured resting screens do not exercise it, so their supplied Axe results do not resolve it.
- **Low, nonblocking — singular serving copy uses a plural label.** Screenshots: pwa-home-phone.png, pwa-home-phone-dark.png and pwa-recipes-phone-dark.png show “1 servings”; pwa-calendar-phone-de-dark.png shows “1 portionen.” Source: frontend/src/Calendar.tsx:77 and :311; frontend/src/Recipes.tsx:74. This is minor language polish and does not impede the captured tasks. Imported recipe titles correctly remain in their source language.

No material clipping, unreadable body/placeholder colour, misleading demo household data, decorative dashboard metrics or deviation requiring a rebuild was found in the required captures.

## Required fixes

Give each `Sheet` instance a stable unique heading ID and set the dialog's `aria-labelledby` to it (for example, React `useId`). Keep the visible heading and native modal/focus behavior. Acceptance: every open Sheet has role `dialog` and an accessible name matching its visible title; opening and Escape/close still restore focus to the invoking control. Verify the name on an existing planning or confirmation sheet with an accessibility-tree assertion or focused dialog accessibility check.

Use the single permitted fix batch, then recapture the same seven-screen matrix for the verdict pass. No aesthetic change or additional visual variant is required. The plural-copy observation is optional follow-up polish, not a second blocking request.

## Limits

This is an independent manual visual/source finish review. No application files were changed, no new visual variants were run, no Taste AI credit or preference write was used, and no design detector or design-hook pass is claimed. The unavailable specialist/launcher caveat in the packet remains applicable.

The packet's Chromium smoke and captured-screen Axe results are supplied verification evidence; they were not independently rerun here. Static captures cannot establish motion quality, complete keyboard behavior, every dialog/empty/error state, larger text layouts, physical iPhone/WebKit behavior or complete accessibility compliance. This verdict does not establish Web Push, passkeys, QR UI, complete original-master acceptance, or live Bring/AI completion. It covers only the inspected screenshots and relevant source paths.
