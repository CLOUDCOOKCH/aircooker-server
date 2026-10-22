# Recipe ideas UI review

Date: 2026-10-22. Verdict supplied by the fresh read-only finish reviewer: **ship
within the reviewed Recipe ideas UI scope**. No material findings or required UI fixes
remain at this scope. The reviewer opened all five actual captures and inspected the
final feature source and incumbent design authorities. This verdict does not establish
whole-product readiness, publication, live-service, physical-device or security acceptance.

## Scope and design authority

The user requested an AI recipe button for entered home ingredients or random ideas,
explicitly extending the earlier feature freeze. This is an ordinary Operate extension
of the existing Mealf PWA. PRODUCT.md, DESIGN.md and the PWA surface brief retain their
authority; there is no new approved comp, seed, design card or replacement visual world.

Home and Recipes shortcuts open a dedicated task page inside the six-destination shell.
The implementation keeps the original peach and lowercase wordmark, cream/coral/peach
Flo treatment, existing After Dark/Sunday theme roles, system type, solid forms and
glass navigation. Desktop shows request controls beside proposals; at the existing
800px breakpoint they stack. Mode labels wrap on narrow phones, provider destinations
can break anywhere, and proposal text uses constrained columns. The narrowest proposal
thumbnail reduces to 64px within the established original-peach placeholder treatment.
These are local layout adaptations, not new tokens or a system refresh.

“Use what I have” accepts the user's ingredients. “Surprise me” sends an empty ingredient
string, including when earlier typed text remains locally. The page displays the exact
configured household provider, model and base URL and requires explicit consent.
Configuration changes fail closed and require renewed consent. Personal ChatGPT-plan
connections are not a fallback or alternate billing source for this feature.

The household AI produces three complete proposals. Each shows its title/description,
expandable ingredients and “Review recipe”; the ordinary editor exposes quantities,
servings and instructions for correction before explicit Save. Generating or reviewing
does not mutate the recipe library, calendar or Bring! list. Save uses the existing
durable local library/outbox flow, including offline editing. Provider/model provenance
is retained; no nutrition, source attribution or dish photo is invented. The warnings
about extra ingredients and checking AI output remain visible and literal.

Inputs, the request UUID and downloaded proposals persist in browser household storage.
New generation is disabled offline; cached proposals remain readable and editable.
Busy/queued, configuration-change, offline and failure feedback are represented in
source. The five captures do not depict every state. See the
[feature guide](../RECIPE_IDEAS.md) for configuration, privacy, queue and retention behavior.

## Review and evidence provenance

The fresh finish reviewer returned the bounded ship disposition after a read-only
source/capture review. This separate documentation handoff read PRODUCT.md, DESIGN.md,
the PWA surface brief and feature guide; inspected `.impeccable/design.json`,
`frontend/src/RecipeIdeas.tsx`, App.tsx editor routing, Calendar.tsx Home shortcut,
Recipes.tsx shortcut/editor, styles.css, i18n.ts, `src/mealf/recipe_ideas.py` and
`scripts/recipe_ideas_browser_smoke.py`; and opened every capture below. It checked
the supplied logs `build/ideas-pytest.log`, `build/ideas-frontend-tests.log` and
`build/recipe-ideas-browser.log`. It did not rerun tests, recapture screens or run
another browser verification pass.

The captures preserve the incumbent hierarchy, type and glass/solid material treatment.
German wrapping at 390px and 320px is an accepted adaptation. Full-document captures
retain fixed phone navigation at its original viewport position, producing an overlaid
document band. The reviewer checked existing bottom space in source; that band alone
does not establish an inaccessible last item. Static captures do not establish motion
quality, screen-reader delivery or physical-device behavior.

The context launcher and detector were attempted in this session but their launchers
were absent. Existing project context and the Impeccable document reference were read
directly. No launcher, automated design detector, design-hook or plugin-schema pass is
claimed. The documentation adds feature authority/evidence only; it does not regenerate
DESIGN.md or its sidecar.

## Genuine capture record

These are actual Chromium renders of the real PWA with synthetic household data and
explicitly labelled synthetic provider proposals. Provider HTTP is replaced by a
double; the backend, SQLite, durable worker and browser flow are real. Desktop viewport
is 1440×1000, ordinary phone viewport 390×844, narrow phone viewport 320×740.
Full-document image heights can exceed viewport heights.

| Capture | Observed state and image size | SHA-256 |
| --- | --- | --- |
| [Desktop input](../../.impeccable/review/recipe-ideas/ideas-input-desktop.png) | English Flo, entered ingredients, destination and unchecked consent; 1440×1000 | `90425f4d687dcfa79cb8cfc1040a7c353dc13330196b1cb27845cfe5b83ae1d0` |
| [Desktop ready](../../.impeccable/review/recipe-ideas/ideas-ready-desktop.png) | English Flo, three proposals and explicit review actions; 1440×1092 | `baada3da656715f806da24c3c50927e75e920009853a0c52301bed101e1bd768` |
| [German surprise phone](../../.impeccable/review/recipe-ideas/ideas-surprise-phone-de-dark.png) | After Dark, surprise mode, destination/consent and three proposals; 390×1688 | `53d0380cd5714640fc31473bfc08c5ac8560ca7d98de920a508b3c40629c5561` |
| [German 320px surprise phone](../../.impeccable/review/recipe-ideas/ideas-surprise-phone-320-de-dark.png) | After Dark, wrapped modes/destination and narrow proposal layout; 320×1932 | `6667de91a2c43be4bd38fc14a87222c711d4ad333ca0af1bed9811744914c0a2` |
| [German offline phone](../../.impeccable/review/recipe-ideas/ideas-offline-phone-de-dark.png) | After Dark, disabled generation, offline guidance and cached proposals; 390×1664 | `c5a1f12614a4751ff73e6a9dbf4cc34e26172256b02adc1285bed74344fe657e` |

## Supplied local validation and limits

Implementation evidence reports 408 passing backend tests, 59 passing frontend tests,
frontend build/type checks, Ruff lint/format, mypy across 50 source files and generated
OpenAPI drift checks. The test logs inspected here confirm the 408/59 counts. The
browser log records a pass, and the inspected assertions exercise ingredient and
surprise privacy, three complete previews, no automatic library Save, explicit reviewed
offline Save, reload and reconnect sync, cached offline proposals and malformed-output
failure without another saved recipe. Backend tests cover configuration pinning,
UUID replay, interrupted-job recovery, schema rejection, redaction, retention and all
seven adapters over synthetic HTTP. These are supplied run results, not new runs by
the reviewer or documenter.

The browser script runs Axe with WCAG 2 A/AA and WCAG 2.1 AA tags on the English desktop
ready page and German After Dark 390px surprise page. The 320px case checks document
horizontal overflow and captures layout only: **no 320px Axe run is claimed**. The
browser log's compressed “DE320 phone and Axe” wording must be read with that scope.
Automated checks do not establish complete manual accessibility acceptance.

Live AI inference, provider account eligibility, billing and model compatibility remain
unverified. Physical iPhone/Safari, native UI, all-theme/all-state acceptance and a
dedicated security audit are outside this review. Exact-source CI and publication for
this feature are pending at this handoff; earlier releases do not certify these bytes.
The implementation remains unpublished at this documentation checkpoint.

## Preserved design-document drift

DESIGN.md still includes five-destination prose, older navigation/layout measurements
and historical system-only appearance guidance. The project-owned design.json snapshot
also retains five-destination and historical responsive/calendar statements; later theme
guidance records Flo/After Dark/Sunday. These pre-existing snapshot conflicts are not
instructions to undo the six-tab shell or theme library. This handoff preserves both
files and appends the current feature authority to the PWA surface brief without repair.

Preserved SHA-256: DESIGN.md
`a1ed87ec5c749605e329f1fbc79860d26f823d295e132f7f4788177dc6b97af8`;
`.impeccable/design.json`
`b9ccc9ccbe9a0e0759c5e5bd8dc467038edba10a4b3d0dadb434d09659d57d99`.
