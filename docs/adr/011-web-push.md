# ADR 011: opt-in standards-based PWA reminders

Status: accepted implementation direction; live vendor/platform verification outstanding.
Date: 2026-10-21.

PWA-first delivery cannot reproduce native offline scheduled notifications. Use optional
standard Web Push with per-device consent/preferences, household civil times and the existing
SQLite queue/one-container worker. No third repository, broker, Apple membership or mandatory
notification SaaS account. Keep native reminder code for later.

Use pinned pywebpush encoding and py-vapid signing for proven Web Push cryptography, while
owning the HTTPS transport: explicit vendor allowlist, public DNS checks/socket pinning,
TLS verification, no redirects and bounded timeout. Do not use the library's requests send.
Subscriptions and VAPID keys use the existing encrypted vault. Generic payloads keep recipe
content out of notifications; status separates vendor acceptance from device delivery.

Recheck sessions/preferences/meals/time before each send. Durable receipts prevent ordinary
replay, stable Topic/tag limit crash duplicates, and a 15-minute window avoids backlog spam.
Offline preferences are durable drafts, applied explicitly online. See REMINDERS.md for DST,
retry limits, setup/recovery, privacy and remaining device/vendor gates.

Costs: requires connectivity/platform delivery, conservative supported endpoint list,
additional MPL/MIT/Apache dependencies with attribution/source obligations, and no exactly-once
promise. Real encryption and browser receiver tests do not replace live Safari validation.
