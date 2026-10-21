# Use mealf as a PWA

mealf is the new product name, formerly aircooker. Existing installation and storage
identities are preserved. See BRANDING.md for compatibility and the pending original icon files.

The primary client is the browser application in this repository. The native SwiftUI code
is retained in aircooker-ios for a future release. A Mac, Apple Developer membership,
TestFlight and App Store submission are not needed to build or install this web client.
This remains a development release; the complete master acceptance checklist is not met.

## Open and install

Build/run the existing Docker Compose deployment and configure a valid HTTPS ingress.
Set `BASE_URL=https://kitchen.example.org` to the **origin only**, without `/app/` or a
trailing application path. Both the API and client must share that origin. Open
`https://kitchen.example.org/app/`. The existing administration console remains at `/`.
Cloudflare Tunnel and a correctly configured HTTPS reverse proxy are supported deployment
patterns; see DEPLOYMENT.md. Do not disable certificate validation or expose browser login
over untrusted plain HTTP. Chromium's loopback testing exception is not a deployment policy.

For a new household, choose Open your kitchen, enter the local one-time setup token from
`/data/config/setup-token`, choose credentials and an IANA household time zone. Setup locks
transactionally after the first successful account creation. Existing households sign in
with their shared account; each browser has its own stable device and revocable session.
The initial screen names the connected household before sign-in.

On iPhone, open the URL in Safari, use Share → Add to Home Screen, then open its icon.
On other supported browsers, use their Install app option when available. A QR code
containing this public HTTPS URL can be scanned with the phone's normal camera; this build
does not include an in-app QR scanner or privileged pairing token. No password belongs in a QR.

Explore the demo is optional, uses a separate local database and never creates a household,
changes server records or contacts AI/Bring!. Its food artwork and recipes are illustrative.
Leaving it returns to onboarding. Household data is never seeded with sample recipes.

## Everyday use

Home shows actual meals, a civil-week selector, upcoming meals and planning status. Use
Recipes to create/search/edit recipes and choose photos. Ingredients accept explicit decimals,
fractions and ranges; leave unquantified amounts blank and use preparation text for “to taste”.
Serving changes in details recalculate ingredient quantities, not source nutrition values.
The editor retains an unfinished draft on this device, including its selected image.

Calendar has Monday–Sunday navigation and breakfast/lunch/dinner. On narrow screens, select
a day in the anchored week strip; wide screens show the week in a horizontally scrollable
planning grid. A meal's menu provides a non-drag move/duplicate/remove/cooked alternative.
Dragging is an additional control, not the only way to move meals. Week options copy a day
or week, save/apply templates and remove saved templates. Repeat settings edit bounded rules;
individual occurrence changes add exceptions and detached entries. Existing leftovers are
not duplicated through copy/template operations.

Record cooked leftovers from a meal and schedule available portions from Calendar. Local
transactions prevent two browser tabs from overbooking them; the server enforces the same
constraint between devices. Pantry staples affect the backend's Bring! ingredient projection.
Temporary pantry inclusions are bound to a Monday–Sunday shopping period and expire for
the following week, using the household time zone.

Dinner suggestions use local recipes, ratings, cooked history, occupied slots, variety and
available leftovers without AI. Review before approval. Approval is queued as one immutable
batch with a history checkpoint. The backend checks occupied slots transactionally; a
cross-device collision keeps the local preview blocked for review. Settings can archive it
and generate a new preview. Shared category/portion/repetition/leftover defaults and bounded
learning from explicitly approved plans are implemented; see PLANNING_PREFERENCES.md.

Imports accept URLs or supplied content. Structured extraction precedes optional configured
AI. AI requires an explicit content-disclosure checkbox. Social adapters cannot bypass
private content or platform restrictions. Editable previews are never silently saved;
review quantities, servings and extraction warnings and choose Save. A failed source keeps
its URL/text and offers manual creation. A manually completed fallback retains the source
and supplied text; its old import request can be cancelled separately. Source-image import
and broader HTML/social extraction remain partial. Local cancellation is durably sent to
the backend on the next foreground sync.

Bring! is configured in administration. The PWA never handles Bring credentials or calls
Bring directly. The backend owns persistent reconciliation jobs and retries; unverified
connector capabilities keep automatic mutations disabled. Home/Settings expose the actual
configuration state. Manual reconciliation is offered only when the connector reports
safe automatic mutation support. No live Bring!/AI integration is claimed.

Pantry staples marked available are excluded from ingredient requirements. “Include in
shopping this week” overrides that exclusion for the current Monday–Sunday week in the
household time zone. It expires automatically for the following week. An offline change
keeps the week you selected, even if it reaches the server after rollover.

Calendar → Week options saves the selected week as a reusable template. Use its edit button
to rename it or add, remove and change meals, weekdays, recipes and portions. Saved edits
work offline and survive reload. Cancel leaves the saved template unchanged. Applying a
template adds its meals to the currently selected week; editing the template itself never
changes existing calendar meals. Templates cannot copy already cooked leftover portions.

## Offline operation and recovery

Open online once so the public application shell can finish caching. Recipes, meals, pantry,
leftovers, templates, imports, editor drafts, photos and outgoing mutations use IndexedDB.
Photos are cached when viewed; an unseen server image may be unavailable offline. Local
recipe writes, their selected photo and outgoing mutation share a transaction. Failed local
writes preserve the draft. A permanently rejected photo upload blocks its affected recipe,
not unrelated edits; retry it or recover the current recipe as a new copy in Settings.

Sync runs while the app is open, on reconnection/foreground and periodically while visible.
It does not rely on iPhone Background Sync. Once a calendar change reaches the backend,
Bring!/import jobs continue even after the browser closes. The status bar reports offline,
pending, synchronising or rejected changes. Source-device clocks do not decide conflicts:
the last valid server-committed change wins. Tombstones prevent stale edits resurrecting
old identities. Rejected recipe edits can become a new copy or use the retained server
version; the previous local record and queue are archived first.

Server identity/history checks run before uploads or pushes. After a restore, Settings →
Recover server history explicitly archives local records/queued work before adopting a
verified, anchored server snapshot. Photos and unfinished editor drafts remain. Recipe
copies can be restored from archives. Non-recipe archive reconstruction remains manual
using the recovery export; full guided reconstruction is not implemented.

Export unsynchronised work produces a versioned browser recovery JSON including records,
queue, named editor drafts, import requests, archives and base64 photos (100 MiB media limit).
It contains private household content, but no session or integration secrets. Store it
privately. It is an inspection/manual-recovery format, **not** the backend's portable household
archive and is not automatically imported by the browser. Use administration for tested
household JSON/ZIP export/merge. Server backups do not include edits still on an offline device.

Browsers may evict data. Request persistent storage in Settings, sync regularly and keep
exports; a request can be refused by the browser. Signing out revokes the current browser
session and hides cached records; pending work is retained for the next sign-in. It does
not encrypt or erase the browser's site storage. Avoid shared unlocked devices. Remote
revocation cannot remove a disconnected browser's already cached content.

## Platform limits and unfinished work

Incoming iPhone Share Target, WidgetKit widgets and native local biometric locking are not
available in this PWA. Paste a URL/text to import; use normal camera scanning to open a URL.
Passkeys would provide a different Face ID-assisted sign-in and are not implemented here.

Opt-in Web Push reminder controls, durable scheduling/retries and offline settings drafts
are implemented. See [setup, privacy, delivery limits and evidence](REMINDERS.md). They need
permission, an installed Home Screen app on iPhone and connectivity; the PWA does not schedule
offline local notifications. Live vendor/physical iPhone delivery remains unverified.

Actual iPhone/Safari Home Screen, storage lifecycle, passkeys and vendor push delivery need
platform testing. Chromium phone emulation is not an iPhone test. See PWA_IMPLEMENTATION.md
for implementation/evidence status and the remaining master-project gates.

## Development without a Mac

Use Node 24+ and the existing Python 3.12+ backend environment:

```sh
cd frontend
npm ci --ignore-scripts
npm run api:generate
npm run typecheck
npm run format:check
npm test
npm run build
cd ..
python -m aircooker
```

Open `/app/` through your HTTPS development ingress. Vite's optional dev server proxies
`/api` to loopback port 8080 for foreground UI iteration; it does not supply the built service
worker. Use the built client served by Python for offline/install acceptance tests.

```sh
python scripts/pwa_browser_smoke.py
```

Install `requirements-browser.lock` and Chromium/Chrome first. The script uses a temporary
household, actual persistence/auth/API/job processing and explicit synthetic content, with
no external-service credentials. `AIRCOOKER_CAPTURE=1` saves genuine screenshots to the
directory in `AIRCOOKER_SCREENSHOT_DIR`. The browser test also runs axe WCAG A/AA checks on
its stated screens; this is not a comprehensive manual accessibility or Safari certification.

The build emits dependency notices and a licence inventory, and rejects drift from
`frontend/licenses/bundled.json`. The service worker caches an explicit public-build allowlist
under `/app/`; API/auth/private media never enter it. Updates wait for an explicit reload;
an active editor must be finished or left with its retained draft first. Only the initiating
tab reloads on activation. Node and npm packages do not ship as a running production service.

## Shared suggestion choices

Settings → Meal suggestions configures categories, optional fixed portions, repeats and
leftovers for the household after a connected save. Offline edits remain drafts; local
suggestions use the last saved cached choices and approval history. Every proposed plan
remains a preview until explicit approval. Recovery exports include preference/reminder
drafts for manual reconstruction. See PLANNING_PREFERENCES.md.
