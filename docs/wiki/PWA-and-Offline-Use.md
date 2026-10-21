# PWA and offline use

MealF's primary client is the installable browser app at your public HTTPS origin's
`/app/` path. The administration console remains at `/`. Use the same origin for the
client and API; see [Installation](Installation) and [HTTPS and reverse proxy](HTTPS-and-Reverse-Proxy).

## Install on a device

1. Open `https://meals.example.com/app/` and sign in with the household account.
2. On iPhone/iPad, use Safari → Share → **Add to Home Screen**, then open the new icon.
   On a supported desktop/Android browser, use its **Install app** option.
3. Open the app online once and let it synchronise. View photos you will need offline.
4. In Settings, request persistent browser storage where supported. Browsers can refuse
   the request or later evict data, so keep exports and synchronise regularly.

A QR code can contain the public HTTPS app URL for easy opening. It must not contain
passwords, setup tokens or session secrets. The optional demo has a separate local
database and does not create or populate a real household.

## Use recipes and the calendar

Create or edit recipes in Recipes. Ingredients support explicit amounts, fractions and
ranges; leave unknown quantities blank rather than inventing measurements. Recipe details
can scale ingredient quantities to the chosen servings. Review every import before saving;
see [AI recipe import](AI-Recipe-Import) for media and provider requirements.

Calendar supports Day, 3 days and Week views. Move meals by their grip or use the meal
menu's move form. Multi-day views scroll horizontally. Week options copy plans or apply
saved templates; copying does not duplicate already cooked leftovers. Record leftover
portions and schedule them without overbooking the available amount.

Pantry staples marked available are excluded from Bring! requirements. **Include in
shopping this week** overrides this for the household's current Monday–Sunday week.
Meal suggestions use the cached recipe library, ratings, history, variety and leftovers
without AI. Shared suggestion preferences apply after an online save. Proposed plans
remain previews until you explicitly approve them.

## What works offline

Recipes, meals, pantry, leftovers, templates, editor drafts, import requests, selected
photos and outgoing changes are held in the browser's IndexedDB. Local edits survive
reload and wait for foreground synchronisation. An unseen server photo may be unavailable
offline. AI extraction, website fetching, initial sign-in, integration changes and new
notification connections need the backend/network.

The service worker caches only public build files. It does not cache authenticated API
responses or private media; private records/photos use the app's separate local database.
Offline storage is private content on the device, not an encrypted native Keychain.

## Synchronisation and conflicts

Sync runs while the app is open, when reconnecting/returning to the foreground and
periodically while visible. It does not depend on iPhone Background Sync. Once a change
reaches the backend, durable import/Bring! jobs continue even if the browser closes.

Watch the status bar for pending, offline or rejected work. Server commit order determines
accepted updates, rather than device clocks. A permanent failure for one photo/recipe
can block that item while other changes continue. Review the rejection in Settings;
recover the affected recipe as a new copy or retain the server version where offered.
Do not clear browser storage to resolve a blocked queue.

After a server database restore, the app can detect changed history and stop old queued
changes. **Recover server history** explicitly archives local records and queued work
before adopting an anchored server snapshot. Recipe copies can be restored from these
archives; reconstruction of other archived record types remains manual.

## Preserve work before recovery or an update

Use **Export unsynchronised work** in Settings before changing devices, clearing site
data or attempting recovery. This browser recovery JSON includes local records, queued
edits, drafts, archives and available photos, but no session or integration keys. Store
it privately. It supports inspection/manual recovery; it is not the server household
archive and is not automatically reimported. A server backup cannot contain edits that
have never left an offline device.

For a PWA update, finish active edits, accept the update prompt and close/reopen the
installed app as needed. Do not uninstall or clear storage with pending work. An OS icon
may stay cached longer than the page. Signing out revokes the session and hides retained
work; it does not erase or encrypt browser storage. Remote revocation cannot remove data
from a disconnected device.

## Platform limits

Optional [meal reminders](Meal-Reminders) require permission, connectivity and supported
browser services. The PWA does not provide offline local alarms, native Share extensions,
WidgetKit widgets, native biometric locking or passkeys. Physical iPhone/Safari behaviour
and live push delivery remain unverified by the Linux/Chromium tests.

Source: [PWA guide](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/PWA.md),
[mobile calendar](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/MOBILE_CALENDAR.md)
and [planning preferences](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/PLANNING_PREFERENCES.md).
