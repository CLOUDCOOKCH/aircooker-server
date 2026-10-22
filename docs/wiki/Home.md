# MealF Wiki

MealF is a self-hosted household meal planner with an installable browser app (PWA).
One backend container serves the PWA at `/app/`, the administration console at `/admin/`,
the API and a durable background worker. SQLite and private configuration live in one
persistent `/data` volume. Cloudflare Tunnel or another HTTPS reverse proxy provides
the public entry point.

This is a **development preview**. Review the
[implementation status](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/IMPLEMENTATION.md)
and the notes for the image or source revision you deploy. A feature documented from
source may not yet be included in a published image. Live AI/Bring! compatibility and
physical iPhone behaviour have not been established by synthetic or Linux browser tests.

## Set up a new installation

1. Follow [Installation](Installation) to choose a prebuilt image or build from source.
2. Configure [Cloudflare Tunnel](Cloudflare-Tunnel) or an
   [HTTPS reverse proxy](HTTPS-and-Reverse-Proxy).
3. Complete [First-run setup](First-Run-Setup) with your private setup token.
4. Install the [PWA](PWA-and-Offline-Use) and create your first recipe and meal.
5. Set up [backups](Backup-and-Recovery) before relying on stored household data.

You need Docker Engine with Compose v2, persistent local storage and a valid HTTPS
hostname. No Mac, App Store account or mandatory AI subscription is required.

## Configure optional features

- [Configuration](Configuration): origins, time zones, proxy trust and server settings.
- [AI recipe import](AI-Recipe-Import): cloud OCR/extraction, configurable providers and review.
- [Bring! integration](Bring-Integration): optional shopping-list synchronisation.
- [Meal reminders](Meal-Reminders): optional notifications on each browser device.

## Operate the installation

- [Backup and recovery](Backup-and-Recovery): exports, sensitive backups and restoration.
- [Upgrades and maintenance](Upgrades-and-Maintenance): updates, retention and rollback.
- [Troubleshooting](Troubleshooting): common problems and safe diagnostic information.

The household uses a shared account with independent device sessions. There are no
default credentials or separate administrator roles. Keep the data volume, container
logs, tunnel credentials and exports private. Never run two backend instances against
the same SQLite volume.

The product was previously called **mealf**. Existing package, Compose, API and
storage names retain that identifier for compatibility; do not rename volumes during
an upgrade. See the [branding and compatibility notes](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/BRANDING.md).
