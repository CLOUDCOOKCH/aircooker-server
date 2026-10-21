# Shared planning preferences: manual finish review

Date: 2026-10-21. Method: fresh manual screenshot and source review. This is the
bounded finish handoff for household suggestion preferences and the multi-category
suggestion preview. The Impeccable context launcher, detector and documentation/review
specialist were unavailable; no automated detector, overlay, plugin schema validation
or specialist pass is claimed. This is not an Impeccable critique-command run.

**Final verdict: ship at the tested shared-planning UI scope.** The initial P1
approval finding is resolved by one bounded fix and confirmation pass; no required
UI fixes remain. The associated P2 recovery wording is also resolved. The approved
glass/forest-green/system-type direction is preserved, and no visual redesign or
additional aesthetic exploration is needed. This is scoped acceptance, not complete
product acceptance.

## Evidence inspected

Read `.impeccable/surfaces/pwa.md`, `PRODUCT.md`, `DESIGN.md`, `AGENTS.md`, README and
implementation status, plus current `frontend/src/PlanningSettings.tsx`, Suggestions
in `Calendar.tsx`, `model.tsx`, `lib/preferences.ts`, `lib/planning.ts`, relevant shared
CSS, translations and Sheet semantics. Read the local batch validator and server
approval implementation only to assess the consequence of repeated approval.

All three images were opened with `view_image`; the German phone image was also
inspected at original resolution:

| Genuine browser capture | Dimensions | Reviewed state |
| --- | --- | --- |
| `docs/screenshots/pwa-planning-settings-desktop.png` | 1440 × 2320 full document; 1440 × 1000 viewport | English/light, shared saved defaults, three categories, repeats enabled, leftovers disabled, 3.5 portions |
| `docs/screenshots/pwa-planning-settings-phone-de-dark.png` | 390 × 3580 full document; 390 × 844 viewport | German/dark, same saved defaults and wrapped controls |
| `docs/screenshots/pwa-planning-preview-phone.png` | 390 × 1128 full document; 390 × 844 viewport | English/dark, internally scrolling preview of an offline week, visible category and serving labels |

SHA-256 at review:

```text
64f7c9597fcdcf0d26b4fb2f0dc08264a3877be9bab277ed369c66d03a49f74c  pwa-planning-settings-desktop.png
e247b27591912a795d8b0d0a26712412e06cf60cdb6f29e06109cd4adb8707e7  pwa-planning-settings-phone-de-dark.png
2b5101539f872be41b415d7ab2ca431f50e32c1a9a2e32210a6e36446caac12a  pwa-planning-preview-phone.png
```

The current browser-flow evidence supplied by the implementation run passes
cross-device preferences, offline draft reload, 21-meal preview/approval and server
acceptance learning against real first-party APIs, without service doubles in that
script. The reviewer inspected the corresponding assertions in
`scripts/pwa_browser_smoke.py`; this review did not rerun the browser flow. These
successful single-activation assertions initially did not exercise repeated approval
while the first local commit was pending. The bounded confirmation run added that
coverage, as recorded below.

## Initial finding and bounded confirmation

**P1 — Repeated or changing approval while the local commit is pending: resolved.**
At initial review, `Suggestions.approve()` in `frontend/src/Calendar.tsx:980` entered asynchronous
`app.save()` without an in-flight guard. The approval button at line 1080, regeneration
button and row checkboxes remained enabled. Two rapid activations could both inspect the
same unoccupied React snapshot and create separate meal UUIDs and separate approval
request IDs before the first commit refreshed that snapshot. `LocalStore.saveBatch()`
validates leftover reservations and recipe existence, but does not prohibit two
non-leftover optimistic meals occupying the same slot. The server safely rejects the
second occupied-slot batch; it does not make the second client operation the same
idempotent request. This can turn one intended approval into duplicate optimistic
work and a rejected-batch recovery task. This consequence is established by source
inspection; a rapid-activation runtime reproduction has not been executed here.

The bounded fix now sets a synchronous `approving` ref before its first await and
releases it in `finally`. Busy state disables approval, regeneration and selection;
the dialog exposes `aria-busy`, disables Close and blocks Escape dismissal during the
commit. Its guarded close callback also protects the same-turn window before React
renders busy state. Occupancy is reread from persisted local meals. Failure retains
the selected set and the guard is released for retry; existing server slot/replay
protections remain in place. These failure/close branches were verified in source,
not by injected runtime failures or a screen-reader session.

The reviewer inspected the final component/Sheet sources, the executable new browser
assertion in `scripts/pwa_browser_smoke.py` and the successful run output at
`/tmp/mealf-planning-browser-guard.log`. The real browser run invokes
`button.click(); button.click();` in one turn, then directly checks IndexedDB for
exactly 21 queued mutations sharing one non-null approval request ID. On reconnect,
the real server contains exactly the expected 21 added meals and learning counts of
one. This exercises the original risk rather than only asserting disabled markup.
The reviewer did not independently rerun it. The idle capture hashes are unchanged;
the fix changes pending/error behavior, not the reviewed idle composition. No second
aesthetic pass was opened.

| Bounded issue | Result | Evidence |
| --- | --- | --- |
| P1 repeated approval / changing selection during commit | Resolved | Synchronous guard, busy/close semantics, real rapid-activation/local-queue/server assertions |
| P2 misleading generic preview error | Resolved | Specific English/German recovery copy inspected in source |
| Required fixes remaining | 0 | Bounded confirmation only |

## Findings that pass at the reviewed scope

- **Layout and responsiveness:** the section fits the established solid Settings
  groups, keeps the shared-purpose explanation ahead of controls and places the
  explicit save action after the draft guidance. Desktop columns remain balanced.
  The German phone's long repeat and fixed-portions wording wraps without clipping
  or horizontal overflow. Native checkbox labels provide a larger activation area
  than the checkbox glyph alone. Full-page captures show fixed navigation at the
  original viewport position; that alone is not a content-overlap defect. The
  visible focused skip link in Settings is an existing keyboard focus state and
  temporarily covers part of the first category in these captures.
- **Honest state/copy:** English and German distinguish saved household preferences
  from per-device offline drafts and say that previews use the last saved choices.
  The component saves the draft independently, disables connected save offline,
  validates before PUT and clears the draft only after refreshing persisted
  preferences. The success copy preserves the separate plan-approval step. Demo
  copy explicitly scopes its preferences to the isolated demo. No automatic meal
  application or live-service claim is introduced.
- **Categories and quantities:** Breakfast/Lunch/Dinner are explicit checkbox
  labels; the empty-category helper and disabled save expose the minimum selection.
  Fixed portions reveal a visibly labelled field, comma input is normalised and
  incomplete draft input survives parsing. Preview rows show weekday, category,
  actual recipe title, quantity and ranking reason. Singular/plural serving labels
  are count-aware. German wording and the retained period decimal display are
  understandable; the latter is not a blocker.
- **Review before apply:** individual native checked rows let the user exclude
  meals; zero selection disables approval; regeneration resets selection to the
  new preview. The button says “Add to calendar” / “In den Kalender übernehmen”.
  Existing-slot checks and atomic server application prevent silent replacement
  of scheduled meals. The 21 rows use internal dialog scrolling; the initial
  capture does not show its bottom actions, but the browser flow locates and
  activates the approval button successfully.
- **Semantics/readability:** native labels, fieldset/legend, checked/disabled states,
  named Sheet dialog and close control preserve the established keyboard model.
  Preference success uses `role="status"`; preference and preview errors use
  `role="alert"`. Text and controls retain the approved neutral/green theme pairs,
  visible hierarchy and legible dark surfaces. No image conveys required
  information beyond its adjacent recipe text. The busy approval semantics are
  now included in the resolved bounded fix above.

## Bounded observations and evidence limits

The preview's initial generic error message (“Check the highlighted fields…”) did
not identify a changed/occupied slot or storage failure. The bounded fix replaces it
with task-specific English/German guidance to check the calendar before trying
another mix, without asserting that no write occurred. This resolves the P2 recovery
observation in source. This review does not require another aesthetic pass.

Captures show saved preference controls and one offline preview, not every error,
loading, empty-category, stale/shared-write or incomplete-number state. Those paths
were assessed from source. No independent full keyboard traversal, screen-reader
session, text enlargement, all-state/composited contrast measurement or motion
acceptance was performed. Existing Axe/browser evidence is scoped to its executed
screens; it does not establish complete accessibility compliance.

This review accepts neither the complete product nor physical Safari/iPhone,
native parity, live external services, production release or original logo artwork.
The exact supplied peach icon/wordmark remain blocked as recorded in
`docs/BRANDING.md`; existing interim assets and the approved visual direction are
not reopened. No product source was changed by this review.
