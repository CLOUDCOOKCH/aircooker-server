# PWA screen guide

The 2026-10-22 UX rework keeps the original Mealf peach, wordmark, glass navigation and
Flo, After Dark and Sunday themes. All six main destinations remain. The native app and
administration console are unchanged by this PWA layout work.

Genuine German After Dark browser captures: [Home](screenshots/pwa-ux/home-phone.png),
[Calendar](screenshots/pwa-ux/calendar-phone.png),
[Settings](screenshots/pwa-ux/settings-phone.png). See
[capture provenance and limitations](screenshots/pwa-ux/provenance.json).

## Everyday tasks

- **Home** starts with the selected day's meals. Use the date arrows or Today to change
  the day, Plan a meal to schedule food, or the labelled import/create/inspiration actions
  below the meals. The weekly overview, suggestions and recipe-book shortcuts remain.
- **Calendar** groups the week strip and Day / 3 days / Week choices above the board.
  Today returns to the household's current civil day. Tools contains copy/template actions.
  Suggest meals and moving-meal guidance follow the board. Multiple-day views scroll
  horizontally on narrow screens. The drag grips and explicit move/copy editor both work.
- **Recipes** puts Import and New recipe beside the page title, followed by search,
  name/rating sorting and Recipe ideas. Recipe details link directly to ingredients and
  method; servings scaling and planning remain available.
- **Recipe editor** begins with name and servings. Timing, rating and other metadata live
  in an expandable details group. Ingredients and method have direct section links.
  The Save bar stays above phone navigation; the draft indicator distinguishes a locally
  retained draft from an explicitly saved recipe. Closing a group does not erase its fields.
- **Import** starts with a URL or a photo/screenshot source. Open “Paste recipe text or
  upload a file” for other content, or the importing guide for details. Existing provider
  consent, source uncertainty and explicit review/Save continue to apply.
- **Pantry** keeps staple entry and availability controls visible; its longer explanation
  is expandable. **Shopping list** retains quantities, pantry exclusions and Bring status
  with a manual Sync to Bring! action. It does not become an independent shopping service.

## Settings

Open the named section before editing its controls:

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
blocked work remains visible for review. Do not clear browser storage, reinstall the PWA
or delete Docker volumes as part of updating the layout.

## Verification and limits

`scripts/pwa_ux_browser_smoke.py` uses a real disposable server, SQLite, browser sessions
and mutations. It checks the six destinations, disclosure navigation, English/German,
the three themes, search/rating sorting, recipe anchors, retained optional fields and
offline recipe Save/reload/reconnect. It runs Axe and checks document width at desktop,
390px and 320px; the narrow calendar keeps an explicitly scrollable internal board.
The existing import, notification, shopping, conflict and recovery suites still apply.
Synthetic provider/Bring/push responses in those suites are not live integration evidence.
The screenshot recipe data is synthetic and the chicken artwork is the existing original
demo illustration, not a photograph of an actual cooked recipe.

Local Chromium checks do not establish physical iPhone, camera, installed-PWA keyboard,
VoiceOver or live-service acceptance. The API, database schema and native contract are
unchanged. Final review and exact-source publication status are recorded in
[implementation progress](IMPLEMENTATION.md); this is still a preview product.

`ghcr.io/cloudcookch/mealf-server:poc-20261022.9` is published for AMD64/ARM64. Exact-source
CI also passes Linux WebKit layout/theme/image-import/OCR/offline checks. Both fresh native
image gates, public checksums/config identities, anonymous pull and the published .8-to-.9
same-volume 5152 upgrade pass; [release evidence](validation/github-pwa-ux-preview.json).
Retain your volume and port/command/healthcheck configuration, save editors and accept the
PWA update on each device. The evidence above does not establish physical-iPhone acceptance.
