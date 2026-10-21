# Meal reminders

MealF offers optional per-device Web Push reminders. They need a reachable backend,
HTTPS, browser permission and connectivity. They are best-effort notifications, not
offline alarms. Live push-vendor and physical iPhone delivery remain unverified by the
automated receiver tests.

## Enable reminders on a device

1. Open the signed-in PWA. On iPhone/iPad, first add it to the Home Screen using Safari
   and open the installed app.
2. Go to **Settings → Meal reminders**.
3. Choose **Connect notifications** and allow the browser's permission prompt.
4. Enable meal reminders, select categories/times and save while connected.
5. Use the test-send control and check both server status and the actual device.

MealF does not request notification permission on launch. Each browser device connects
independently. You do not need an Apple developer account, APNs certificate, Firebase
project or extra backend container. Browser/OS policy determines whether Web Push is
available on a particular device.

Changing a reminder form stores a local draft, including offline. Only an explicit
connected save changes server delivery. A pending draft does not update another device.
Disconnect removes the server and browser subscriptions; OS permission is managed in
the browser/device settings. A revoked/expired session needs sign-in and reconnection.

## Scheduling rules

Times use the saved **household time zone**, even while your device travels. Each enabled
category gets at most one recorded accepted reminder per household date when it has an
uncooked meal. The worker checks once per minute. Cooking, removing or moving a meal,
disabling its category or signing out suppresses pending delivery when next checked.
An externally accepted notification cannot be recalled.

After an outage, reminders catch up only within 15 minutes of their scheduled time.
Older reminders are discarded. Spring DST gaps shift a time forward across the gap;
the autumn repeated time uses its first occurrence. Changing the time after acceptance
does not send the same day's category again.

Temporary failures retry with bounded backoff, respecting the delivery window and
bounded vendor `Retry-After`. Eight unsuccessful attempts can mark a job failed. A
404/410 subscription requires reconnection. **Last accepted by delivery service** means
the vendor accepted an HTTP request; it does not prove the device displayed a message.
Standard Web Push cannot guarantee exactly-once delivery after a crash/retry.

## Network and privacy

Permit outbound DNS/HTTPS from the backend to the supported vendor endpoints:

- Apple: hosts under `*.push.apple.com`.
- Chromium: `fcm.googleapis.com`.
- Firefox: `updates.push.services.mozilla.com`.

Other endpoints fail explicitly rather than becoming arbitrary network destinations.
TLS verification and public-address validation remain enabled. This outbound path is
separate from your inbound Cloudflare Tunnel or reverse proxy.

Notifications use generic English/German text and a date or Settings link. They omit
recipe titles, ingredients and household names, but may still appear on a lock screen.
The vendor can observe delivery timing and connection metadata. Web Push is optional;
no subscription means no reminder traffic.

The server generates its VAPID key and encrypts it at `/data/config/webpush-vapid.enc`.
Subscription credentials are also encrypted. Preserve the database, config vault and
installation key together in a protected volume backup. Household JSON/ZIP exports
exclude notification subscriptions. Reconnect devices after a clean household import
or when a recovered installation has a different VAPID key.

## If a reminder does not arrive

Check permission, installed-app support, Focus/battery settings, connectivity, server
health, saved preferences, household time zone, an uncooked meal in the selected category
and per-device delivery/job status. Reconnect an expired subscription explicitly. Do
not treat successful synthetic tests or vendor acceptance as proof of background OS display.

Source: [reminder architecture, evidence and platform links](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/REMINDERS.md).
