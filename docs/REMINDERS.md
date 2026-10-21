# Optional PWA meal reminders

Settings → Meal reminders connects this device's browser notification service. Nothing is
requested on launch: choose **Connect notifications**, allow the browser prompt, enable meal
reminders, choose categories/times and save. Disconnect removes the server subscription and
then the browser subscription. OS permission remains under the browser/device's control.

On iPhone/iPad, add mealf to the Home Screen in Safari and open that installed app first.
A valid public HTTPS `BASE_URL`, a reachable running backend and connectivity are required.
No Apple developer membership, APNs certificate, Firebase project or extra container is
required for standards-based Web Push. Browser/OS delivery is best effort, not an alarm
clock: Focus settings, permissions, connectivity and platform policy can delay/prevent it.
There is no offline local notification scheduler in the PWA.

## What is scheduled

Preferences are per browser device, not shared household settings. Each enabled category gets
at most one accepted reminder per household civil date, when it has an uncooked meal. All
categories use the configured household time zone even when a device travels. Cooking,
removing or moving a meal, disabling its category or signing out suppresses pending sends
when the worker next checks. An already accepted external notification cannot be recalled.

The periodic worker checks once per minute. After a restart/outage it only catches up within
15 minutes of the configured time. Older reminders are discarded rather than delivered as a
backlog. Spring DST gaps shift the chosen local time forward across the gap; autumn overlap
uses the first occurrence. Receipts are keyed by subscription/date/category, so changing a
time after acceptance does not send that day's category twice. At civil midnight, the next
household day becomes eligible. Recurrences use the same bounded calendar expansion.

Settings changes persist locally as a draft immediately, including offline/reload. Save
while connected explicitly applies them on the server. A local draft does not silently alter
server delivery. `navigator.onLine` is a hint; network failures retain the draft and report an
error even if the browser still reports online. New-device permission, connection and test
sending require connectivity. A new sign-in must reconnect a revoked/expired connection.

## Delivery and errors

SQLite stores leased, deduplicated jobs across restarts. Temporary failures retry with
bounded exponential backoff; vendor `Retry-After` is respected up to one hour. Meal sends
still check their 15-minute window before retrying. Jobs stop after eight unsuccessful
attempts; Settings shows failed/pending counts and a per-device manual retry. A 404/410
subscription is disabled and requires reconnecting. HTTP 429, network errors and changed API
responses are surfaced as safe error codes, never silently reported as delivered.

“Last accepted by delivery service” means an HTTP success from the push vendor, **not proof
of display or receipt on the device**. Notification payloads contain only the mealf name,
generic English/German text and a calendar date or Settings link. Browser language is saved
when connection/preferences are saved. Recipe titles, ingredients and household names are
excluded. Opening a notification focuses an existing application where possible; an active
recipe editor is preserved and the user opens the reminder after finishing their edit.

Standard Web Push has no exactly-once delivery guarantee. A crash after vendor acceptance
but before recording the SQLite receipt can resend. Stable vendor Topic and browser tag
collapse/replace such messages where supported. No purchased-item or Bring! state is involved.

## Security, deployment and recovery

Authenticated device-scoped APIs use the existing cookie/CSRF/origin controls or native
bearer authentication. Mutation budgets and a 50-active-device cap bound abuse. The server
accepts HTTPS/443 endpoints only under `*.push.apple.com`, `fcm.googleapis.com` and
`updates.push.services.mozilla.com`. Other browser vendors fail clearly instead of becoming
arbitrary network destinations. Every send resolves the vendor, rejects non-public DNS
answers and pins the TLS socket to the verified address; redirects are not followed. TLS
hostname verification, ten-second transport timeout and bounded payload/TTL remain active.
Response bodies are closed without downloading. No shell, requests-based send or imported
URL is involved. These restrictions may require adaptation for future browser endpoints.

Allow outbound DNS/HTTPS to the configured push vendors. The browser talks to its own vendor
when subscribing; the backend sends encrypted content with an installation-specific VAPID
key. The vendor can observe connection metadata, timing and opaque subscription identifiers;
it is not an analytics provider chosen by mealf. Notifications may appear on a lock screen.
Web Push is fully optional; no configured subscription means no reminder traffic.

Subscription endpoints/auth keys are encrypted in SQLite. The generated VAPID private key is
encrypted at `/data/config/webpush-vapid.enc` using the existing restricted vault key. Status
exposes only the public VAPID key, a one-way endpoint fingerprint and safe operational fields.
Endpoints, keys and payloads are not logged or included in household JSON/ZIP exports. A
secret-bearing volume disaster backup must protect both database and the entire config vault;
see BACKUP.md. Deleting the vault breaks credential decryption. A clean household import has
no subscriptions; reconnect each device. If a restored/new installation changes its VAPID
key, Settings detects the browser key mismatch and requires disconnect/reconnect, rather
than claiming it is connected. Ordinary container upgrades preserve the key in `/data`.

Delivery receipts and jobs are conservatively retained with existing queue history; bounded
retention/quotas remain a release task. A shared-account user has household privileges; the
app does not claim separate account roles or remote deletion of offline site data.

## Evidence and limits

Unit/integration tests exercise real Web Push payload encryption/decryption, real VAPID
signature verification, pinned sockets/DNS rejection, encrypted storage, session expiry,
CSRF/rate limits, replay, device isolation, export exclusion, DST, retries and obsolete-meal
suppression. `scripts/push_browser_smoke.py` exercises actual PWA/API/IndexedDB controls,
offline drafts, notification navigation and the real service-worker receiver using a
CDP-injected event. Its subscription and vendor transport are **explicit synthetic doubles**;
permissions are test-granted/denied. No live vendor, actual user permission dialog, physical
iPhone, Safari delivery, background OS display or Focus interaction has been verified.

The CI browser job runs both the full ordinary PWA flow and this separate labelled reminder
flow; artifacts contain genuine browser captures of synthetic household data. See the newest
reminder validation report for exact commit/count/image/CI scope. No full product acceptance
or stable release is enabled by these results.

## Primary-source research (reviewed 2026-10-21)

- [Apple: sending Web Push in web apps/browsers](https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers)
- [WebKit: iOS/iPadOS Home Screen Web Push](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/)
- [MDN: subscription and user activation](https://developer.mozilla.org/en-US/docs/Web/API/PushManager/subscribe)
- [Mozilla: push endpoint and protocol](https://mozilla-services.github.io/autopush-rs/http.html)
- [pywebpush: replaceable encoding/VAPID dependencies](https://github.com/web-push-libs/pywebpush)

These establish documented capabilities, not verification that a particular device/vendor
will accept and display this implementation. A credential-free HTTPS deployment and real
browser/device smoke test remain necessary before promising live reminders.
