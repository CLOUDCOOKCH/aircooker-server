# Shopping UI finish review

Date: 2026-10-22. Scope: the PWA Shopping page, its Home/Calendar/Settings entry points, Bring! compatibility confirmation, manual reconciliation feedback, ingredient states and cached offline display. This is an ordinary extension of the established operating interface; no new visual world, approved comp, seed or design card is introduced.

**Disposition: ship within the reviewed Shopping UI scope.** The supplied fresh independent `shopping_finish_reviewer` returned persistence **pass**, TYPE/MATERIAL/GROUND **match**, and thesis/story/form **match**, with the quality ceiling reached and no material UI fixes required. This documentation handoff directly inspected the sources and opened all four captures. It records the separate reviewer and browser evidence without rerunning their workflow, and does not establish whole-product readiness or security acceptance.

## Authority and inspected sources

The [product requirements](../../PRODUCT.md), [design reference](../../DESIGN.md), [project-owned design snapshot](../../.impeccable/design.json) and [PWA surface brief](../../.impeccable/surfaces/pwa.md) remain authoritative. Shopping preserves the original artwork, system typography, shared Flo/After Dark/Sunday theme roles, solid reading surfaces and glass navigation with the existing five destinations. The prominent manual Bring! action and literal setup, status, ownership, failure and cached-data copy fit the existing operating purpose.

Direct source inspection covered `frontend/src/Shopping.tsx`, `frontend/src/lib/shopping.ts`, the Shopping rules in `frontend/src/styles.css`, English/German Shopping keys in `frontend/src/i18n.ts`, and entry points in `frontend/src/App.tsx`, `frontend/src/Calendar.tsx` and `frontend/src/Settings.tsx`. The browser smoke script and its local `build/shopping-browser.log` were also inspected. Historical DESIGN layout descriptions, including the older selected-day-only mobile Calendar, and system-only appearance descriptions are superseded by later mobile-calendar and theme-library entries. That documentation drift is recorded here without repairing or regenerating `DESIGN.md` or `.impeccable/design.json`.

## Genuine browser captures

All four source captures in `.impeccable/review/shopping/` were opened with `view_image`. They show synthetic household/list data rendered by real Chromium. Desktop viewport: 1440×1000; phone viewport: 390×844. Captures are full-document images, so image height can exceed viewport height. Fixed phone navigation remains at its original viewport position over one document band; this capture behavior alone does not establish permanent content obstruction. German phone wrapping is an accepted responsive adaptation. Ingredient fixture names retain their source language.

| Capture | Image pixels | Reviewed state |
| --- | --- | --- |
| [shopping-unverified-desktop.png](../screenshots/shopping/shopping-unverified-desktop.png) | 1440×1068 | English current-week requirements, blocked manual sync, configuration link, collapsed compatibility disclosure, unsent ingredients and pantry-exclusion count |
| [shopping-synced-desktop.png](../screenshots/shopping/shopping-synced-desktop.png) | 1440×1000 | English connected list, prominent manual sync, last successful reconciliation, manual Rice left unchanged and Tomatoes synced |
| [shopping-synced-phone-de-dark.png](../screenshots/shopping/shopping-synced-phone-de-dark.png) | 390×1186 | German After Dark page, full-width manual action, wrapped row states, pantry exclusion and ownership guidance |
| [shopping-offline-phone-de-dark.png](../screenshots/shopping/shopping-offline-phone-de-dark.png) | 390×1313 | German After Dark cached reload, explicit calculation timestamp/local-edit warning, disabled Bring! action and retained ingredient states |

SHA-256 of the reviewed bytes:

```text
shopping-unverified-desktop.png    5eee237a2e8b7a530626b67eb6eecea413704263202e1c1c566df4da18817630
shopping-synced-desktop.png        3abfde35153c9c4636b294f2b5b6d4d463080959a698cb96d8898907415ad7bf
shopping-synced-phone-de-dark.png  f92a5f1015c7611f305a3d3e8120316b250799bcf62a177051c0a44287a32214
shopping-offline-phone-de-dark.png 9b3e90e90d507537f6c88127a6943c66e573c03b6db5ce2ff2e182a485b55aad
```

## Behavior and visual continuity

- **Entry and hierarchy:** Home's Bring! status, Calendar's Shopping action and Settings' Bring! row open the same page with Back navigation, current household Monday–Sunday period, concise calculation explanation, list connection state, manual sync and divided ingredient rows. Shopping remains a task page within the existing five-tab shell. The 880px content maximum and restrained dividers preserve the incumbent hierarchy without introducing decorative panels.
- **Manual action and verification:** the primary action is visually prominent and becomes full width on phones. Source disables it while offline, stale, busy, queued/running, verifying or not ready. Compatibility disclosure requires explicit confirmation of a dedicated test list before the temporary item check; its literal copy describes add/update/complete/remove, list-specific verification, 30-day expiry and possible cleanup after failure. Loading Bring! lists alone does not enable writes. The expanded consent flow is exercised by the supplied browser run, rather than pictured in the collapsed desktop capture.
- **Reconciliation and ownership:** source first synchronizes local edits and blocks reconciliation if pending mutations remain. Queued work, failures and the last successful reconciliation have distinct wording; failure does not claim success. Ingredient labels distinguish not sent, update pending, synced, purchased this week, removed in Bring! and matching manual items left unchanged. The footnote explains last-server-state ownership and weekly suppression; pantry exclusions remain a disclosure. The captures show the manual/synced distinction, while other item states were inspected in source.
- **Cached and responsive display:** the last parsed server snapshot persists through the existing local store. Offline/stale display warns that recent local edits may be missing and shows the calculation time; it does not imply a fresh local projection. The phone layout stacks connection controls and permits long list names and state labels to wrap. Native checkbox/disclosure controls, status/live feedback and alert errors are present in source. Not every loading, empty, error, verification or ingredient-state branch is captured.

## Supplied verification and limits

The inspected `build/shopping-browser.log` reports **PASS** for real PWA/server/worker shopping projection, explicit dedicated-list verification, failed then successful manual sync, manual-item preservation, English desktop/German dark phone checks with Axe, and offline cached reload. The inspected script uses real application requests and worker processing with a synthetic Bring transport, asserts preservation of the manual Rice item and one Tomatoes item, checks phone horizontal bounds, and runs Axe against `main` for WCAG 2 A/AA and 2.1 AA tags. These are supplied local browser results; this documentation pass did not execute them again.

Bring responses are synthetic. No live Bring! mutation, physical iPhone/Safari validation, exact-source CI pass or publication pass is claimed for this extension. The launcher and automated detector were attempted but absent; no launcher/detector pass is claimed. The independent finish review is a separate supplied review. Static captures and scoped Axe checks do not establish complete keyboard, screen-reader, motion, text-enlargement or accessibility acceptance. No material UI fix remains within this bounded review; live-service, device, complete-product and security acceptance remain separate.
