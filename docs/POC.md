# Mealf preview

## Candidate: pantry and food tastes

`poc-20261023.3` is selected for the pantry/taste extension but **has not been published**.
The repository Compose default points to this candidate; do not assume it can be pulled.
For an available preview, explicitly set
`MEALF_IMAGE=ghcr.io/cloudcookch/mealf-server:poc-20261023.2` before the install commands
below. `.2` remains the last published preview; its completed gates do not certify `.3`.

Candidate source `58c5930` plus the narrow German pantry CSS correction adds actual-stock
pantry onboarding, resumable shared tastes and shorter import preparation. Local 472
backend / 75 frontend tests and real Chromium workflows pass with synthetic integrations;
the manual scoped review resolves its one P2 finding. Both current-source architecture
build/runtime/security and Chromium/WebKit CI, release images, anonymous pull and the
candidate persistent-volume upgrade remain pending. A local Docker build was blocked by
workspace Alpine-download HTTP 403. See [implementation evidence](IMPLEMENTATION.md),
[food setup operations](FOOD_SETUP.md) and [bounded review](validation/food-setup-review.md).
Keep existing volumes, browser storage and custom `5152:5152` command/healthcheck settings.
Save open work and accept a PWA update only after installing a published image. This
candidate does not establish live AI/Bring!, physical-iPhone or production-v1 acceptance.

## Published preview: everyday navigation and quick planning

`poc-20261023.2` is published and verified for **AMD64 and ARM64**. See
[exact source, image and upgrade evidence](validation/github-quick-planning-preview.json).
Older published-preview entries below retain their historical scope.

The PWA has four primary tabs: Today, Plan, Recipes and Shopping. Settings opens
from the account button with Back; Pantry lives inside Shopping. Empty Plan slots offer
local title search, rating-first recipes and guarded one-tap default portions, with
separate Meal options for date/category/portions/leftovers/recurrence. Real leftover IDs,
portion caps, actual planned-date markers, compact day rows and a separate mobile
sync-status row preserve the existing EN/DE, three-theme, offline-first interface.
Original artwork and route/storage/API/database/native contracts remain unchanged.
Cooking mode is outside this pass. See [screen guide](PWA_UX.md) and
[fresh scoped review and genuine captures](validation/quick-planning-review.md).

Local 459 backend / 70 frontend tests, lint/format/types/build/OpenAPI/artwork/licence and
actual Chromium UX/regression checks pass. The full backend rerun used configured EN/DE
OCR data. The independent read-only manual finish review returns ship with no material
fixes. All six exact-main CI jobs pass, including Chromium/WebKit and both architecture
build/security/runtime checks. Fresh image gates, six public asset checksums, native
config identities/SBOMs and anonymous pull pass. A published .1-to-.2 same-volume 5152
upgrade retains identity, session, history and recipes. One offline double-tap meal
survives reload and syncs once, changing its shopping projection from 400 g to 600 g.
Physical iPhone and live-provider/Bring! verification remain open.

Use `ghcr.io/cloudcookch/mealf-server:poc-20261023.2`. Retain the existing volume and custom `5152:5152`
ports, command and healthcheck; save open editors and accept the PWA update on each device.
This source-only UI extension requires no data reset or native-app update. This is a
preview, not production v1 acceptance.

## Published preview: readable AI diagnostics

`poc-20261022.10` is published and verified for **AMD64 and ARM64**.
The connection test reports known provider failures
as failed 422 configuration validation, preserving redacted JSON through proxies that
replace 5xx pages. Quotas remain 429; genuine gateway/server errors remain distinct.
Administration and Recipe ideas show specific English/German recovery and safe codes;
Gemini model fields explain and validate exact API identifiers. See
[troubleshooting](RECIPE_IDEAS.md#troubleshooting-gemini-and-failed-requests) and
[local verification/review](validation/recipe-ideas-errors.md).

Local 445 backend/67 frontend tests, build/types, Ruff, mypy, formatting, OpenAPI drift
and actual Chromium PWA/admin regressions pass with synthetic provider/proxy doubles.
No migration, API-schema, native, credential or sync-identity change is required. Keep
the existing volume, `5152:5152` command/healthcheck and open drafts when updating.
All six exact-source CI jobs pass at `0f1b88e7`, including the full Chromium/WebKit suite.
Both fresh native image scan/runtime executions, six public asset checksums, matching
image identities/SBOMs, provenance, anonymous pull and a published .9-to-.10 same-volume
5152 upgrade pass. Identity, session, sync history, recipes and shopping quantities remain
intact. See [exact evidence](validation/github-ai-diagnostics-preview.json).

Use `ghcr.io/cloudcookch/mealf-server:poc-20261022.10`. Keep the existing volume and
custom `5152:5152` command/healthcheck. Save editors and accept the PWA update.
The user reports a successful small probe with structured output disabled; complete ideas
generation remains unverified. Leave that setting off for now, reopen Recipe ideas,
approve sending to the configured provider and explicitly request a new batch. Reloading
retains the old failed request; it does not generate again. These diagnostics are not a
claim of a repaired Cloudflare tunnel or live-generation acceptance.

## Published preview: PWA UX rework

`poc-20261022.9` is published and verified for **AMD64 and ARM64**.
The rework keeps Mealf's original branding, glass, all themes
and six destinations while simplifying Home, calendar controls, recipe navigation,
imports and Settings. Shopping prioritizes required Bring setup before progress.
See [the screen guide](PWA_UX.md) and [scoped UI review](validation/pwa-ux-review.md).
All six exact-main-source CI jobs pass at `76fe7995`, including 425 backend tests per
architecture, 66 frontend tests and Chromium/WebKit workflows. Both fresh native image
scan/runtime gates, six public asset checksums, image identities/SBOMs, anonymous pull
and a published .8-to-.9 same-volume upgrade on internal port 5152 pass. Instance identity,
active session, history, recipes and shopping quantities are retained; the new Settings
disclosures/report, EN/DE navigation and cached offline shopping work in the pulled image.
See [exact release evidence](validation/github-pwa-ux-preview.json). Physical iPhone and
live-service acceptance remain open; this is a preview, not production v1.

Use `ghcr.io/cloudcookch/mealf-server:poc-20261022.9`. Keep existing volumes and the
custom `5152:5152` command/healthcheck when updating. Save open editors, accept the PWA
update and reopen the app. Clearing browser storage or reinstalling the PWA is unnecessary.

## Published preview: sync reliability

`poc-20261022.8` is published and verified for **AMD64 and ARM64**. It fixes false synced
status, rejects stale/incomplete pull responses, moves record exchange before imports and
adds Settings → Check sync connection. No server data migration or native contract change.
The user's deployed cause remains unconfirmed; see
[troubleshooting and confirmed/unconfirmed scope](SYNC_TROUBLESHOOTING.md).

All six exact-main-source CI jobs pass at `708365b0`: 425 backend tests per architecture,
66 frontend tests, Chromium/WebKit regressions and security checks. Both fresh native image
scan/runtime gates, six public asset checksums, image identities/SBOMs, anonymous pull and
a published .7-to-.8 same-volume upgrade on internal port 5152 pass. Identity, active
session, history and recipe/shopping data are retained. Published PWA diagnostics,
EN/DE navigation and narrow-phone cached offline shopping pass Chromium checks.
Physical iPhone and the actual deployment remain unverified. This is a preview, not v1.

Use `ghcr.io/cloudcookch/mealf-server:poc-20261022.8`. Retain existing volumes and
custom `5152:5152` command/healthcheck. Save editors, accept the PWA update on each device,
and retry Sync now. If changes remain missing, use Settings → Check sync connection →
Copy report. Do not clear browser storage or reinstall the PWA to diagnose this issue.
See [exact source, image and upgrade evidence](validation/github-sync-preview.json).

## Published preview: Recipe ideas

`poc-20261022.7` is published and verified for **AMD64 and ARM64**. Open **Recipe ideas**
on Home or in Recipes. Enter ingredients at home or choose **Surprise me** for three
complete proposals from configured household AI, with explicit consent and review/Save.
Cached proposals and reviewed offline saves persist. No automatic library/calendar/Bring!
changes occur, and personal ChatGPT billing is not used. See [usage/privacy](RECIPE_IDEAS.md).

All six exact-main-source CI jobs pass at 74c1c925: 421 backend tests per architecture,
59 frontend tests, Chromium/WebKit regressions and both security gates. Both fresh native
image scan/runtime/operator gates, six public checksums/config identities, anonymous pull
and a published .6-to-.7 same-volume upgrade on internal port 5152 pass. Identity/session/
history/recipe/shopping projection, six-tab EN/DE navigation and cached offline shopping
are preserved; migration 015 and new Recipe ideas controls/API are present. Generated
proposals use explicit provider HTTP doubles in browser acceptance; live AI/iPhone remain
unverified. The retained native contract passes its independent Linux/macOS/Xcode/simulator
CI; no native Recipe ideas UI is added.

Use `ghcr.io/cloudcookch/mealf-server:poc-20261022.7`, keeping the existing volume and
custom internal/external `5152:5152` command/healthcheck. Save local work, accept the PWA
update and reopen Home or Recipes. See [exact evidence](validation/github-recipe-ideas-preview.json)
and [scoped UI review](validation/recipe-ideas-ui-review.md). This is a preview, not v1.

## Published preview: primary Shopping navigation

`poc-20261022.6` is published and verified for **AMD64 and ARM64**.
Shopping list is a primary sidebar destination and appears as **Shop** / **Einkauf**
in mobile navigation. Existing Home/Calendar/Settings shortcuts select the same page.
The manual Bring! action and cached offline requirements are preserved. Local browser
checks cover keyboard navigation, current-tab state and six non-overlapping 44px targets
with unbroken German labels at 320px. No API, storage or native changes are required.

All six exact-main-source CI jobs passed at c403651: 392 backend tests per architecture,
59 frontend tests and Chromium/WebKit flows. Both fresh native image scans/runtime gates,
six public checksums/config identities and anonymous pull passed. A published .5-to-.6
same-volume upgrade on internal port 5152 preserved identity/session/history/recipes and
shopping quantities; real EN/DE phone navigation and cached offline shopping passed.
Use `ghcr.io/cloudcookch/mealf-server:poc-20261022.6`, retaining the existing volume and
`5152:5152` command/healthcheck. See [exact evidence](validation/github-shopping-navigation-preview.json)
and [UI review](validation/shopping-navigation-ui-review.md). Physical iPhone/live Bring!
acceptance remains open. This is a preview, not production v1.

## Published preview: Mealf identifiers and administration paths

`poc-20261022.5` is published for **AMD64 and ARM64**. Current Python/Swift packages,
modules, targets and operator examples use Mealf. The administration console and its
scripts/styles live at `/admin/`; `/` is free for a separately hosted landing page. The
PWA remains at `/app/`. See [upgrade and path-routing instructions](MEALF_MIGRATION.md).

All six exact-main-source CI jobs pass at 0b6307e: 392 backend tests per architecture,
59 frontend tests, and the Chromium/WebKit regressions. Both fresh native image
scan/runtime/operator gates, six public asset hashes, manifest/config identities,
anonymous pull and the published .4-to-.5 upgrade checks pass. Real previous/new PWA
bundles preserve an offline recipe, image Blob hash, outbox/mutation/device IDs and
session while reusing the existing browser database; cookie refresh issues current names.
The same-volume 5152 upgrade preserves identity/history, pending replay, recipe/photo,
synthetic purchased Bring ledger, real EN/DE OCR previews and clean old ZIP/photo restore.

Use `ghcr.io/cloudcookch/mealf-server:poc-20261022.5`, retaining the existing volume and
custom `5152:5152` command/healthcheck. No PWA reset/reinstall is needed. The former
module entry point is retained as a deprecated bridge for deployed custom commands;
fresh configuration uses `mealf.app:create_app`. Actual GitHub repository names still
require owner renaming in Settings. Native identifiers/contract were updated separately
and passed Linux/macOS/Xcode/simulator CI. Live services and physical iPhone acceptance
remain open; this preview is not production v1.

See [the prerelease](https://github.com/CLOUDCOOKCH/aircooker-server/releases/tag/poc-20261022.5)
and [exact source, scans and upgrade evidence](validation/github-mealf-rename-preview.json).

## Previous preview: recipe photos

`poc-20261022.4` adds original-peach placeholders for missing/unreadable recipe photos and
source metadata pictures for URL/AI imports, including incomplete drafts. Photos remain
editable before explicit Save and cached for offline use. See [recipe photos](RECIPE_PHOTOS.md).
All six exact-source CI jobs pass at e47b107: 383 backend tests per architecture, 55 frontend
tests and real Chromium/WebKit regressions. Both fresh native image scan/runtime/operator
gates, six public asset checksums/config identities, anonymous pull and the published
.3-to-.4 same-volume 5152 upgrade pass. Identity/session/history, pending offline replay,
recipe/photo and the synthetic purchased Bring ledger survive; real EN/DE OCR stays
preview-only and old ZIP/photo restore passes. See [prerelease](https://github.com/CLOUDCOOKCH/aircooker-server/releases/tag/poc-20261022.4)
and [exact release evidence](validation/github-source-photos-preview.json).

Preserve existing volumes and custom `5152:5152` command/healthcheck settings. Save edits,
accept the PWA update and reopen Recipes. Existing recipes gain the fallback immediately;
re-import a source to try retrieving a picture. Live sources/providers and physical iPhone
remain unverified; preview publication is not production-v1 acceptance.

## Previous preview: shopping visibility

`poc-20261022.3` adds the [shopping requirements view](SHOPPING.md), manual **Sync to Bring!**,
per-item/queued/error feedback, an offline snapshot and in-container dedicated-test-list
verification. All six exact-source CI jobs pass: 366 backend tests per architecture,
54 frontend tests and real Chromium/WebKit regressions. Both fresh native image scans,
runtime/operator checks, six public asset checksums/config identities, anonymous pull and
the published .2-to-.3 same-volume 5152 upgrade pass. Identity/session/history, recipe/photo,
offline replay and the synthetic purchased ownership ledger survive; real EN/DE OCR previews
and old ZIP/photo restore pass. See [prerelease](https://github.com/CLOUDCOOKCH/aircooker-server/releases/tag/poc-20261022.3)
and [exact publication evidence](validation/github-shopping-preview.json).

Preserve existing volumes and custom `5152:5152` command/healthcheck settings. Save edits,
accept the PWA update, then open **Calendar → Shopping list**. Loading Bring! lists alone
does not prove safe writes: explicit dedicated-test-list verification is required and
unsupported UUID behavior stays blocked. Live Bring! and physical iPhone remain unverified;
preview publication is not production-v1 acceptance.

## Previous preview: personal ChatGPT

`poc-20261022.2` adds optional personal ChatGPT **text** imports through the official
open-source sign-in flow, a downloadable Windows-friendly loopback helper, encrypted
session-owned credentials, model selection and explicit review before saving. Follow
[the connection guide](CHATGPT.md). The [prerelease](https://github.com/CLOUDCOOKCH/aircooker-server/releases/tag/poc-20261022.2)
is published for AMD64/ARM64. Exact-source CI, Windows helper tests, fresh native scans,
public assets/pull and the published .1-to-.2 same-volume 5152 upgrade/OCR/restore pass.
See [publication evidence](validation/github-chatgpt-preview.json). Live subscription
eligibility/extraction remains unverified; automated external responses are synthetic. Existing `5152:5152` installations
should update only the image and retain their current volume, command and healthcheck.

This is an installable **development preview**, not the finished product or a stable
release. The browser app and self-hosted backend run together in one container on
**linux/amd64** and **linux/arm64**. You do not need a Mac, Xcode or an App Store account.

## Previous preview baseline

`poc-20261022.1` includes the merged configurable AI providers, image/PDF inputs,
Gemini video requests, editable extraction previews, provider settings and operator guides.
The local camera/OCR path remains available without AI. It also freezes the PWA v1 scope
and introduces fail-closed candidate/stable release policy, SQLite storage limits, worker
recovery, verified local backups and explicit offline household deletion. The
[prerelease](https://github.com/CLOUDCOOKCH/aircooker-server/releases/tag/poc-20261022.1)
is published for AMD64/ARM64; native scans/runtime checks, anonymous pull, public assets,
same-volume 5152 upgrade, real local OCR and old ZIP/photo restore pass. See
[exact validation evidence](validation/github-v1-readiness-preview.json). Live providers/Bring/push,
physical iPhone and full production acceptance remain open. See [v1 readiness](V1_READINESS.md).

## Install

Download `compose.preview.yaml` from this prerelease into a new directory. Configure a
valid HTTPS reverse proxy or Cloudflare Tunnel to `127.0.0.1:8080`, then run:

```sh
export BASE_URL=https://meals.example.com
docker compose -f compose.preview.yaml pull
docker compose -f compose.preview.yaml up -d
docker compose -f compose.preview.yaml logs mealf
```

Replace the example domain with your HTTPS origin. Copy `setup_token` from the startup
`setup_required` entry in the container's Logs view; no terminal is needed. Open your HTTPS
origin to complete setup with that token and your own household credentials. Then open `/app/`.
On iPhone use Safari → Share → Add to Home Screen. Desktop Chromium also supports install.
Ordinary HTTP is not supported for browser authentication or offline/PWA installation.
See the [HTTPS/deployment guide](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/DEPLOYMENT.md)
for proxy configuration and forwarded-header restrictions. Do not expose port 8080 publicly.

The preview Compose file uses its own named persistent volume. Keep it across restarts;
`docker compose down -v` deletes that volume. Existing development installations should
retain their existing volume and follow the backup/upgrade guide rather than starting
another container against the same SQLite database. The setup token is a secret: do not
paste it into support issues or commit it.

The last published version tag is `ghcr.io/cloudcookch/mealf-server:poc-20261023.2`. The moving `:preview`
channel is available for intentional preview upgrades. For reproducible installs, set
`MEALF_IMAGE=ghcr.io/cloudcookch/mealf-server@sha256:…` to the digest at the top of the
GitHub prerelease. No `latest-stable` tag is created by preview publication.

The `.2` preview adds `/bin/bash` for NAS/container terminal clients. In your container
manager, choose `/bin/bash` and run `cat /data/config/setup-token` before first-run setup.
For an existing installation, update only the image version and recreate the container with
the same volume and port settings; the token is removed after setup. No default password
or public bootstrap token is introduced. `/bin/sh` remains available.

The `.3` preview prints the existing one-time setup token to the operator's container logs
at each unconfigured startup, so a terminal is optional. After setup the file is removed,
the token is invalid and configured starts stop emitting it. Historical log lines remain;
keep logs private. `LOG_SETUP_TOKEN=false` disables token logging when preferred. Passwords,
session tokens and AI/Bring credentials do not share this logging exception.

The `.4` preview installs the original supplied peach/wordmark in the PWA/console, favicon,
Apple touch icon and manifest icons. Retain existing volumes/port settings on upgrade and
accept the PWA update after finishing an active edit. No browser-data reset is needed.
An installed OS icon may remain cached longer than the page. Protect/synchronise offline
work before any OS-level reinstall. See the
[brand guide](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/BRANDING.md).

The `.5` preview extends the peach identity through the PWA and administration console:
cream/coral/peach light appearance, cocoa/peach dark appearance, shared theme tokens,
glass navigation and solid forms. Login and selected empty states include English/German
food innuendo; setup, security and error instructions remain literal. Update only your image
reference, retain the volume and existing port/command/healthcheck settings (including a
custom `5152:5152` installation), then reload and accept the PWA update after saving edits.

It also blocks ordinary PWA pinch/double-tap zoom while keeping recipes and input fields selectable and scrolling
enabled. Accidental control/label selection is suppressed. Browser/OS keyboard accessibility zoom remains available. Safari/physical-iPhone
behavior is unverified. Publication retries for this version preserve a completed release;
do not rerun an older release expecting to publish newer main-branch changes.

The `.7` preview addresses phone PWA enlargement/clipping: mobile fields are at least
16px, Safari text autosizing is stabilized, and app content, navigation and dialogs
respect notch/home-indicator safe areas in portrait and landscape. Retain your volume
and port settings. Save edits, accept the PWA update and close/reopen the installed app.
No browser-data reset or reinstallation is required. Physical phone confirmation remains
necessary; Linux engine checks are not an actual Home Screen installation.

The `.8` preview adds Day / 3 days / Week calendar views, remembered per device, with
horizontally scrollable multi-day columns and explicit touch/pointer drag grips. Move
meals between dates/categories, scroll at grid/page edges, or tap/focus a grip to use the
existing move form. Moves use the normal durable offline queue and recurrence exceptions.
Narrow dialogs stack Date and Meal fields to prevent native date-input overlap. See
[mobile calendar behavior and evidence](MOBILE_CALENDAR.md). Keep existing data/ports
when upgrading and save edits before accepting the PWA update.

## What you can try

The `.6` preview adds more localized food jokes and a silent peach-slap Easter egg in
the planner and admin console. Tap a peach, or focus it and press Enter/Space, for a
hand-swipe, wobble and rotating comeback. Reduced motion keeps feedback without movement.
The original artwork is unchanged. See [behavior and evidence](PEACH_EGG.md).
Keep your existing volume and custom port/command/healthcheck settings when upgrading,
including `5152:5152`. Save active edits before accepting the PWA update.

- Create/edit recipes with structured ingredients, instructions, images and serving scaling.
- Plan meals in the weekly calendar, use templates, recurrences, pantry and leftovers.
- Review local suggestions and apply them explicitly; configure shared planning defaults.
- Edit cached household data offline and synchronise after reconnecting.
- Import supported public recipe metadata or supplied text, edit the preview, then save.
- Configure the household in the English/German administration console; export/import data.

The glass-style PWA is the primary client. Native iOS code is retained for later.

## Known limits

- Full product acceptance remains incomplete. Use test or backed-up data for this preview.
- Live Bring! and AI accounts were not available for validation. Their adapters have
  synthetic coverage; unsupported Bring! writes remain disabled until compatibility is
  proven. No official Bring! affiliation is implied.
- Social imports cannot bypass private content, authentication or platform restrictions.
  Captions/transcripts remain incomplete. Written-recipe image OCR is available in English
  and German; other layouts/languages and handwriting may require correction/manual entry.
- Web Push is optional and needs connectivity. The receiver/scheduler have automated tests,
  but live push vendors and physical iPhone delivery have not been validated. It cannot
  guarantee timed offline reminders. Native share extensions/widgets are not PWA features.
- Real iPhone/Safari testing is outstanding. Chromium coverage does not prove Safari behavior.
- Supplied peach/wordmark artwork is installed in this PWA/console release. Physical iPhone
  Home Screen icon refresh is unverified; retained native artwork remains separate later work.
- Household deletion is an explicit offline operator command, not an in-app button; read
  [backup/deletion instructions](BACKUP.md) before use. Destructive replacement restore,
  broader archive reconstruction, safe media compaction, expanded resource acceptance and
  the remaining security/release review are incomplete.

## Publication checks

Preview publication requires all six CI jobs to pass on the exact main-branch source SHA:
backend test/type/contract/Docker checks and security on both CPU architectures, plus PWA
core and actual browser workflows. Both release images are then built on their native
architectures, scanned again with the existing unsuppressed HIGH/CRITICAL vulnerability
gate, and exercised with isolated persistent data. The verified image bytes are transferred
to the publication job without rebuilding. The prerelease includes architecture-specific
scan reports, CycloneDX SBOMs and the API contract. GitHub provenance is attached to the
published manifest. Publication success and anonymous pull access must be verified separately;
a configured workflow alone is not evidence of either.

See the [feature/evidence checklist](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/IMPLEMENTATION.md)
and [PWA guide](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/PWA.md).

The `.9` preview adds **Settings → Theme library**. **Flo** preserves the existing
peach/cream appearance and follows the device. **After Dark** stays dark with ink,
oxblood and dusty rose; **Sunday** stays light with linen whites and sage. The console
has the same choices in its header. Choices stay on this browser and origin, work
offline and are separate from shared household data. Original art is unchanged.
See [theme behavior and testing](THEMES.md). Keep your existing volume, port mapping,
command and healthcheck, including `5152:5152`; update only the image reference.
Save edits and accept the PWA update. No browser-data reset or reinstall is required.

The `.10` preview adds **Import recipe → Photo or screenshot → Take photo / Choose image**.
Your server recognizes printed English/German text locally and opens an editable preview;
only Save adds the recipe. Images and jobs persist offline until the server is reachable.
Optional configured AI receives only recognized text after consent. Clear full-recipe images
work best; photos of a finished dish do not provide a recipe. Review quantities and
instructions. See [photo import, privacy and limits](IMAGE_IMPORT.md). Keep the same volume,
port mapping, command and healthcheck, including `5152:5152`; change only the image reference
to `ghcr.io/cloudcookch/mealf-server:poc-20261021.10` and accept the PWA update.
Do not clear browser data or reinstall while local work is pending.
