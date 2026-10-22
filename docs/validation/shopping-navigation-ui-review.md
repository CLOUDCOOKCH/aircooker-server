# Shopping navigation UI review

Date: 2026-10-22. Verdict supplied by the fresh finish reviewer: **ship within this
navigation change**. No material findings or required UI fixes remain at this scope.

The request was “i want the shopping list as a menu point”. This is an ordinary
refinement of the established Mealf operating interface, with no new visual world,
approved comp, seed or design card. The reviewed source is commit
`8d3594c70ca9d09b62ede594e94383236a2ef5b9` before this documentation handoff.
The verdict does not establish whole-product, live-service, device or security acceptance.

## Scope and resulting behavior

The primary shell presents Home, Calendar, Recipes, Pantry, Shopping list and Settings
in that order. Desktop uses “Shopping list” / “Einkaufsliste”; compact phone labels are
“Shop” / “Einkauf”, with full localized accessible names. Shopping uses the incumbent
bag icon, glass navigation and accent-soft selected state. Exactly one destination
exposes `aria-current="page"`. Native buttons preserve keyboard activation.

Home, Calendar and Settings shortcuts select the same Shopping tab and return to the
main view. Shopping is no longer a subordinate view and has no Back action. The tab
change uses the existing scroll-to-top and main-focus behavior. Original PNGs, system
typography, Flo/After Dark/Sunday themes, solid content surfaces, offline cache and
Bring! verification/manual sync/ownership behavior remain within their existing
contracts. The `/app/` and `/admin/` locations and administration behavior are unchanged.

At the existing phone or short touch-landscape breakpoint, the navigation container
uses `min(520px, calc(100vw - 24px - var(--safe-left) - var(--safe-right)))` and 6px
padding. Six equal-flex buttons have 2px gaps, minimum 44px widths and 55px heights.
Compact labels use the existing system stack at 0.63rem. The supplied 320px Chromium
case applies the final ≤360px override: container width
`calc(100vw - 16px - var(--safe-left) - var(--safe-right))`, container padding `6px 4px`,
zero item gaps and zero button inline padding, retaining minimum target sizes. The
geometry assertion checks all six nonoverlapping targets, viewport bounds, single-line
labels and absence of document horizontal overflow.

## Review and evidence provenance

The fresh finish reviewer inspected all five genuine captures once, final source and
the supplied semantic/320px evidence, and returned the bounded verdict above. This
fresh documentation handoff separately opened all five captures and inspected
PRODUCT.md, DESIGN.md, `.impeccable/design.json`, the PWA surface brief, App.tsx,
Shopping.tsx, model.tsx, i18n.ts, styles.css and shopping_browser_smoke.py. It did not
rerun tests, recapture screens or perform another detector pass. The context launcher
was missing; no launcher, automated detector or plugin-schema pass is claimed.

The captures show the selected sixth destination in English desktop light appearance
and German After Dark phone appearance. Their hierarchy, typography and glass/solid
material treatment remain consistent with the incumbent interface. Phone text wraps
within the existing reading layout. Full-document captures retain the fixed navigation
at the original viewport position, which creates an overlaid document band; the band
alone is not evidence that content cannot scroll above it. The unverified desktop
capture retains the main focus outline from the keyboard navigation check. No new
visual direction or untested screenshot comparison is inferred from these images.

## Genuine capture record

All captures use synthetic household/list data and the explicit in-memory Bring!
transport double. They are browser renders, not illustrative comps. Desktop viewports
are 1440×1000; ordinary phone viewports are 390×844; the narrow phone viewport is
320×740. Captures use full-document mode, so image height may exceed viewport height.
Matching review copies are retained in `.impeccable/review/shopping-navigation/`.

| Capture | Observed state | SHA-256 |
| --- | --- | --- |
| [Unverified desktop](../screenshots/shopping-navigation/shopping-unverified-desktop.png) | Selected Shopping destination, disabled sync and compatibility entry | `0259e9bc05dc1f5db50b90240cffe4677c01a88a706ec6b158a4033ce220871c` |
| [Synced desktop](../screenshots/shopping-navigation/shopping-synced-desktop.png) | Selected Shopping, last-success feedback, preserved manual item and synced requirement | `33b1b0c5a195f7ad0713e6f1a735777537d134c01a0ec9d3bf9ba0b3003bbb68` |
| [German After Dark phone](../screenshots/shopping-navigation/shopping-synced-phone-de-dark.png) | Six destinations, Einkauf selected, full-width sync | `0dcf55d7bfa9647e908e006061b109d95ea48cef3bf2d480d68aa179295aab1f` |
| [320px German After Dark phone](../screenshots/shopping-navigation/shopping-nav-phone-320-de-dark.png) | Six compact labels and Einkauf selected at the narrow viewport | `204d584c98f0bee334cb0bfb7882e9d680561fcc1922008d116d57cfcbecec0c` |
| [Offline German After Dark phone](../screenshots/shopping-navigation/shopping-offline-phone-de-dark.png) | Cached calculation warning, retained items and disabled Bring! sync | `70bced71f4edb4d7989c27fc97219557003c6ab58da5057941c3e430fc372780` |

## Supplied local validation and limits

The implementation handoff reports passing 392 backend tests, 59 frontend tests,
TypeScript/build/format checks, Ruff lint/format, mypy and generated OpenAPI drift.
Real Chromium Shopping coverage exercises Calendar shortcut and keyboard primary-tab
activation, one current destination, dedicated-list UUID compatibility verification,
failed then successful manual sync, manual-item preservation, desktop/phone main-region
Axe checks and cached offline reopening. The 320px checks establish six targets of at
least 44×44px with no overlap and single-line labels. Supplied pwa_layout Chromium
phone/landscape/safe-area checks also pass. This document records those results as
supplied evidence; source inspection of assertions does not independently prove a run.
The local WebKit layout attempt was blocked by the missing `webkit-2336/pw_run.sh`
browser executable; no WebKit behavior ran in that attempt. CI installs WebKit, but its
result for this source remains pending here.

The PWA/server/worker flow is real; Bring! network/service responses are synthetic.
Physical iPhone/Safari, live Bring! account/list behavior, complete manual accessibility
and all-theme/all-state acceptance remain unverified. Exact-source CI and publication
are pending at this handoff. Earlier Shopping publication evidence and
`shopping-local.json` belong to their historical source and are not a CI result for
this navigation change. Static captures do not establish motion, screen-reader or
physical-device behavior. Native code and API behavior are outside this refinement.

## Preserved design-document drift

DESIGN.md still says “Preserve five destinations”, records five phone controls and an
older phone-nav width; design.json retains a five-entry destinations array, an older
phone-nav dimension and historical responsive/calendar measurements. Historical
system-only appearance prose predates the fixed After Dark/Sunday choices, although
later appended theme guidance acknowledges them. These are existing snapshot conflicts,
not new visual decisions. This handoff updates only the PWA surface brief and this
review; it preserves DESIGN.md and design.json without a broad design rewrite. The
PWA brief now explicitly records the six-destination navigation and marks the earlier
subordinate Shopping description as historical.

## Reviewed source fingerprints

SHA-256 fingerprints taken during this documentation handoff:

| File | SHA-256 |
| --- | --- |
| `frontend/src/App.tsx` | `1ce9e412bbcc1413a6ab527541b52a8e21765dd9d4b9bdffaeba4f4f8c421e32` |
| `frontend/src/Shopping.tsx` | `9c52e44b167fe32b518c86a0cbeb07a7b9c260f893e2c5dd563a6c8446c1b35f` |
| `frontend/src/model.tsx` | `04ba34cf627d95fe65332f45d619050bc6e6d1afa7d3b43c1edbfb45aa3d4848` |
| `frontend/src/i18n.ts` | `fa43abedeb706dcdeb8093f4078c22fe35808d9074a8f6391d92266e3ba23a7c` |
| `frontend/src/styles.css` | `a1889f79be8ca6e90fcb4d8c2e25135543eb4dbdda2f7d5beb5e32b0b1f93821` |
| `scripts/shopping_browser_smoke.py` | `e7e58b6f44497eb7c79db9ada08164f54cedfca0770a78f492b7667d0cf66c60` |
| Preserved `DESIGN.md` | `a1ed87ec5c749605e329f1fbc79860d26f823d295e132f7f4788177dc6b97af8` |
| Preserved `.impeccable/design.json` | `b9ccc9ccbe9a0e0759c5e5bd8dc467038edba10a4b3d0dadb434d09659d57d99` |
