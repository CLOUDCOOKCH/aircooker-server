# mealf PWA proof of concept

This is an installable **development preview**, not the finished product or a stable
release. The browser app and self-hosted backend run together in one container on
**linux/amd64** and **linux/arm64**. You do not need a Mac, Xcode or an App Store account.

## Install

Download `compose.preview.yaml` from this prerelease into a new directory. Configure a
valid HTTPS reverse proxy or Cloudflare Tunnel to `127.0.0.1:8080`, then run:

```sh
export BASE_URL=https://meals.example.com
docker compose -f compose.preview.yaml pull
docker compose -f compose.preview.yaml up -d
docker compose -f compose.preview.yaml exec mealf cat /data/config/setup-token
```

Replace the example domain with your HTTPS origin. Open that origin to complete secure
setup with the one-time token and your own household credentials. Then open `/app/`.
On iPhone use Safari → Share → Add to Home Screen. Desktop Chromium also supports install.
Ordinary HTTP is not supported for browser authentication or offline/PWA installation.
See the [HTTPS/deployment guide](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/DEPLOYMENT.md)
for proxy configuration and forwarded-header restrictions. Do not expose port 8080 publicly.

The preview Compose file uses its own named persistent volume. Keep it across restarts;
`docker compose down -v` deletes that volume. Existing development installations should
retain their existing volume and follow the backup/upgrade guide rather than starting
another container against the same SQLite database. The setup token is a secret: do not
paste it into support issues or commit it.

The version tag is `ghcr.io/cloudcookch/mealf-server:poc-20261021.2`. The moving `:preview`
channel is available for intentional preview upgrades. For reproducible installs, set
`MEALF_IMAGE=ghcr.io/cloudcookch/mealf-server@sha256:…` to the digest at the top of the
GitHub prerelease. No `latest-stable` tag is created by preview publication.

The `.2` preview adds `/bin/bash` for NAS/container terminal clients. In your container
manager, choose `/bin/bash` and run `cat /data/config/setup-token` before first-run setup.
For an existing installation, update only the image version and recreate the container with
the same volume and port settings; the token is removed after setup. No default password
or public bootstrap token is introduced. `/bin/sh` remains available.

## What you can try

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
  Captions/transcripts and image extraction are incomplete; manual content remains available.
- Web Push is optional and needs connectivity. The receiver/scheduler have automated tests,
  but live push vendors and physical iPhone delivery have not been validated. It cannot
  guarantee timed offline reminders. Native share extensions/widgets are not PWA features.
- Real iPhone/Safari testing is outstanding. Chromium coverage does not prove Safari behavior.
- The mealf display name is installed; the exact new peach icon/wordmark remain pending
  access to the original downloadable PNGs. Existing icons are interim.
- Full household deletion, destructive restore, broader archive reconstruction, safe media
  compaction, quotas and the remaining security/release review are not delivered by this POC.

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
