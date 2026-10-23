# Ingredient editing and compact pantry review — 2026-10-23

**Verdict: ship within the reviewed ingredient-editor and pantry extension. Zero material
findings; no required source changes or recaptures.** Fresh independent read-only manual
finish review supplied from `/tmp/mealf-ingredient-finish-review.md`, followed by this
documentation handoff. The shipped specialist definition was unavailable; these are
manual specialist equivalents, not a shipped-specialist pass.

Implementation `469d83d` is committed; this documentation handoff is not yet committed.
The feature remains unpublished at this handoff. Compose selects candidate
`poc-20261023.4`; `.3` remains the latest published preview. CI/publication are pending.
No immutable source hash or exact-source release acceptance is claimed here.

## persistence

Reviewed PRODUCT.md, DESIGN.md, the PWA surface contracts, scoped runtime/CSS diffs,
IngredientFields, ingredient-options and its tests, and the ingredient browser script.
Name selection patches only the chosen name; the existing ingredient-spreading path
retains imported `original_text`, preparation and quantity metadata. The incumbent
draft and explicit recipe Save paths remain separate.

Native unit selects use stable stored identities with localized labels. Choosing one
does not convert the quantity, guess ingredient density or normalize unknown units.
Imported/custom values retain an editable custom field until explicitly changed.
Suggestions draw on locally available pantry/other-recipe names, with catalogue aliases
and bounded typo matching. Their six-result list remains optional; new typed names
remain allowed and create no phantom pantry stock. Fuzzy matching is not a shopping
identity or Bring ownership operation. No API, database migration, native contract pin
or Bring ledger change is required by this UI extension.

## fidelity

The independent reviewer opened all seven final genuine Chromium captures from
`.impeccable/review/ingredient-picker/`. The documenter opened the four unmodified copies
linked below; [provenance.json](../screenshots/ingredient-picker/provenance.json) records
source paths, SHA-256 values, pixel dimensions and the full seven-capture matrix.

| Capture | Viewport | Interface / theme | Documentation copy |
| --- | --- | --- | --- |
| pantry-desktop | 1440×1000 | English / Flo | [PNG](../screenshots/ingredient-picker/pantry-desktop.png) |
| suggestions-desktop | 1440×1000 | English / Flo | [PNG](../screenshots/ingredient-picker/suggestions-desktop.png) |
| pantry-phone-de-dark | 390×844 | German / After Dark | Source matrix only |
| suggestions-phone-de-dark | 390×844 | German / After Dark | [PNG](../screenshots/ingredient-picker/suggestions-phone-de-dark.png) |
| pantry-320-de-sunday | 320×740 | German / Sunday | Source matrix only |
| pantry-basics-320-de-sunday | 320×740 | German / Sunday | [PNG](../screenshots/ingredient-picker/pantry-basics-320-de-sunday.png) |
| suggestions-320-de-sunday | 320×740 | German / Sunday | Source matrix only |

All are full-document exports with animations disabled. Fixed navigation and sticky
Save remain painted at their initial viewport bands while document content extends
below; their apparent position over later content is not evidence of an obstruction at
the scrolled ingredient field. Pixel height can exceed the original viewport height.

The synthetic household includes a source-platform import fixture with `zwibel`, custom
unit `Handvoll`, original text and an added `Dragon fruit` name. The visible `Zwiebeln`
suggestion and source label, free-name path, custom-unit escape and retained imported
text make the behavior legible. Desktop pantry rows have a 56px minimum; normal mobile
rows are about 92px with ≥44px label actions. Longer names wrap. The basics picker keeps
complete German names at 320px. Decorative food emoji, including the generic bowl
fallback, accompany text and are hidden from assistive technology.

The bounded implementation self-check corrected top-row baseline alignment and stacked
ingredient quantity/unit fields at ≤360px before the fresh independent ship review.
It introduced no comp, raster, identity, palette or typeface; original brand PNGs remain
unchanged. Solid forms, system type and restrained glass navigation continue the approved
world. User-requested pantry emoji are a scoped extension to the historical snapshot's
older emoji prohibition.

Historical snapshot drift is explicitly retained: DESIGN.md/design.json describe five
primary destinations and older layout measurements, while current authority uses four
tabs with contextual Pantry/Settings. The older desktop h1 snapshot is 2.375rem with
−0.035em tracking; task-layout.css currently uses 2rem/−0.03em and denser task layouts.
The snapshot's token listing does not fully describe the implemented fixed After Dark
and Sunday theme overrides, despite its later theme-name narrative. This extension does
not refresh those navigation/layout/type/theme records. Runtime sources, PRODUCT.md and
the scoped surface contracts govern the current implementation.

Preserved byte-for-byte SHA-256:

- `DESIGN.md`: `443b13fa38a9c6e79670df7bcad90fa37e90421dfe52730256ef4dfabdd466b9`
- `.impeccable/design.json`: `b9ccc9ccbe9a0e0759c5e5bd8dc467038edba10a4b3d0dadb434d09659d57d99`

## ceiling

The in-flow combobox/listbox keeps suggestions within the editor layout, with a visible
focus outline, source labels, arrow/Enter selection and Escape dismissal. Native unit
controls plus a custom field remain understandable at narrow widths. The reviewer found
no material visual or interaction defect at this code-led Operate extension's scope.

Implementation-agent evidence, inspected and attributed rather than rerun by the reviewer
or documenter:

- **Passed locally:** 472 backend and 81 frontend tests; Ruff check/format, mypy, contract
  drift, TypeScript/build, Prettier, original-artwork integrity and licence checks.
- **Passed in real Chromium:** the new ingredient workflow with real SQLite and offline
  canonical-name/custom-name/custom-unit Save/reload/sync; original-text retention; no
  phantom pantry records; keyboard/trusted-tap selection; pantry toggles; English/German;
  all three themes; Axe and 1440/390/320 widths. Existing PWA offline/two-device, PWA UX,
  AI-import and food-setup browser suites pass with synthetic providers.
- **Pending:** exact-source CI, publication and WebKit ingredient coverage. The script's
  later CI WebKit/TLS-fixture support does not change UI/captures and has no local WebKit
  pass. Offline reload remains Chromium-only in that script because of the known WebKit
  automation limitation.
- **Unverified:** actual AI/Bring! live services, physical iPhone/Safari, motion quality,
  screen-reader behavior and complete-product acceptance. Static screenshots establish
  none of these.
- **Unavailable:** context launcher and detector attempts exited 127; no design hook,
  detector, plugin-schema or shipped-specialist validation pass is claimed.

The documenter inspected supplied `/tmp/mealf-ingredient-*.log` artifacts for tests,
build/format, final ingredient browser capture run, the current Chromium smoke check,
PWA, UX, AI imports and food setup. Their successful outcomes support the attributed
local results above; the reviewer's test evidence was supplied separately. Temporary
logs and review input are session artifacts, not durable public release evidence.

## material_fixes

None. Zero material in-scope findings, with no required source correction or recapture
after the independent review. This verdict does not certify unrelated historical drift
or the entire product.

## keep

Keep optional local name suggestions and explicit selection, free new names, stable
units and the custom escape, exact quantity/imported original text, explicit recipe Save,
offline drafts/outbox, dense pantry rows with retained action targets, decorative emojis
paired with text, original artwork and Bring ownership boundaries. See the
[ingredient guide](../INGREDIENT_EDITING.md) for user-facing behavior.
