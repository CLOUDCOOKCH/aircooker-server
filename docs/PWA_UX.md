# PWA screen guide

The 2026-10-23 navigation and quick-planning extension has four primary tabs:
**Today, Plan, Recipes and Shopping** (German: **Heute, Plan, Rezepte, Einkauf**).
Settings opens from the persistent account button; Pantry opens inside Shopping.
The original Mealf peach, wordmark, glass navigation and Flo / After Dark / Sunday
appearances remain. `poc-20261023.2` is published and verified for AMD64 and ARM64;
see [exact-source, image and upgrade evidence](validation/github-quick-planning-preview.json).
See the [scoped finish review and exact limits](validation/quick-planning-review.md).

Genuine current browser captures: [Plan](screenshots/quick-planning/calendar-phone-de-dark.png),
[English meal picker](screenshots/quick-planning/meal-picker-phone-flo.png),
[German dark meal picker](screenshots/quick-planning/meal-picker-phone-de-dark.png),
[320px meal options](screenshots/quick-planning/meal-options-phone-320-sunday.png),
[Shopping](screenshots/quick-planning/shopping-phone-de-dark.png) and
[320px Settings](screenshots/quick-planning/settings-phone-320-de-dark.png).
[Provenance and checksums](screenshots/quick-planning/provenance.json) identify the original
capture files, dimensions and source fingerprints. These show a disposable synthetic household.

## Everyday navigation

- **Today** starts with the household's current civil day when you tap its tab. Date
  arrows and Today select another day or return to the current one. Meals lead into
  labelled import/create/inspiration actions, the weekly overview and recipe shortcuts.
- **Plan** opens the existing Calendar screen. The week strip marks dates that actually
  contain meal occurrences, including recurrence exceptions, rather than decorating every
  day. Day / 3 days / Week and Tools remain above the board. Day meals use compact rows;
  multiple-day views scroll horizontally on narrow screens. Drag grips and explicit
  move/copy controls remain available. Suggestions, Shopping and leftovers follow the board.
- **Recipes** keeps Import and New recipe beside the title, followed by search,
  name/rating sorting and Recipe ideas. Recipe details have ingredients/method links,
  serving scaling and planning. The editor retains expandable metadata, draft feedback
  and a Save bar above phone navigation; collapsing a group does not erase its fields.
- **Shopping** retains current-week quantities, pantry exclusions, Bring! readiness and
  manual Sync to Bring!. Open **Pantry** here to edit staples and availability; Shopping
  stays selected and Back returns to it. Shopping does not replace the Bring! service.
- **Settings** opens from the account button in the header. Its Back action returns to
  the preceding primary destination. Phone branding, sync action and account button share
  the first header row; truthful sync status occupies its own row below.

Existing `home`, `calendar`, `recipes`, `shopping`, `pantry` and `settings` route identities,
deep links, stored preferences and offline records remain compatible. Visible tab labels
change without an API, database or native-app change. The administration console is unchanged.

## Quickly plan a meal

1. Open an empty Plan slot. The picker shows the selected date/category and locally
   searches recipe titles. Recipes sort by rating first, then title; Show more recipes
   reveals further results. A no-match message lets you refine the search.
2. Tap a recipe row to add it immediately using the saved household portions preference,
   or the recipe's servings when no household default is set. A guarded save prevents
   rapid repeated activation from adding the same assignment twice. Successful addition
   closes the picker and shows confirmation; offline additions remain in the durable outbox.
3. Use the separate **Meal options** button for that recipe to change date, category,
   portions, leftovers or recurrence before explicitly saving. Choose another recipe
   returns to the picker. Busy controls and dismissal are disabled during the local save.

When available, **Use your leftovers** offers direct assignments. Each choice retains the
real leftover record ID, caps portions at the available amount and adds no recurrence.
Existing recipe-to-plan and leftover-to-plan detail routes remain available. Cooking mode
is outside this extension and has not been implemented.

## Imports and Settings

Import starts with a URL or photo/screenshot. Open “Paste recipe text or upload a file”
for other sources, or the importing guide for details. Provider consent, uncertainty,
editable review and explicit Save continue to apply.

Open the named Settings section before editing its controls:

| Task | Section |
| --- | --- |
| Language and starting screen | Your household |
| Sync now, connection report, sign-in and sign-out | This device |
| Flo / After Dark / Sunday | Theme library |
| Shared portions and variety preferences | Meal suggestions |
| Device notification preferences | Meal reminders |
| Household AI providers and models | AI recipe import |
| Optional personal connection | Your ChatGPT plan |
| Bring configuration and shopping shortcut | Bring! |
| Installation instructions | Make yourself at home |
| Persistent storage and private pending-work export | Offline storage |
| Advanced restore handling | Recover server history |

Blocked work and recovery archives appear when they exist. Expanding or collapsing a
section retains mounted forms and draft values. Connection failures open This device;
blocked work remains visible for review. Keep browser storage, existing Docker volumes
and deployment port/command/healthcheck settings when updating; save open editors and
accept the PWA update on each device.

## Verification and limits

Local real Chromium checks cover the four tabs, account/Back, Pantry selected state,
quick-picker search/default portions, offline double activation/reload/once-only sync,
custom portions/recurrence and real leftover ID/portion caps. The UX suite runs Axe and
width checks at desktop, 390px and 320px in English/German and the three themes. The
existing import, shopping, conflict, recovery, touch drag and safe-area regressions pass.
Inactive navigation labels now use semantic ink after a composited-glass contrast failure;
the final theme/Axe checks pass. See the [review](validation/quick-planning-review.md)
for the complete local evidence and its attribution.

The screenshots are unmodified Chromium captures; normal screens use full-document
capture from the top, while dialogs use viewport-only capture to match their backdrops.
Fixed navigation remains at its original viewport position in a long image. The chicken
is an existing original generated demo illustration, not a photograph of actual cooking.
No new shipping raster or replacement branding was introduced.

All six exact-main CI jobs pass, including Chromium/WebKit and both native architecture
builds, security scans and runtime tests. Fresh image gates, six public asset checksums,
image identities/SBOMs and anonymous pull pass. A published .1-to-.2 same-volume upgrade
preserves identity/session/history/recipe/shopping data on internal port 5152. A rapid
double activation creates one offline meal, survives reload, syncs once and updates the
400 g shopping requirement to 600 g. See the [release evidence](validation/github-quick-planning-preview.json).
These checks do not establish physical iPhone, camera, installed-PWA keyboard, VoiceOver
or live Bring!/AI/Web Push acceptance. The PWA remains a preview product.
