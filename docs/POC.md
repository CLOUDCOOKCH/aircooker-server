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

The version tag for this preview is `ghcr.io/cloudcookch/mealf-server:poc-20261021.9`. The moving `:preview`
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
  Captions/transcripts and image extraction are incomplete; manual content remains available.
- Web Push is optional and needs connectivity. The receiver/scheduler have automated tests,
  but live push vendors and physical iPhone delivery have not been validated. It cannot
  guarantee timed offline reminders. Native share extensions/widgets are not PWA features.
- Real iPhone/Safari testing is outstanding. Chromium coverage does not prove Safari behavior.
- Supplied peach/wordmark artwork is installed in this PWA/console release. Physical iPhone
  Home Screen icon refresh is unverified; retained native artwork remains separate later work.
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

The `.9` preview adds **Settings → Theme library**. **Flo** preserves the existing
peach/cream appearance and follows the device. **After Dark** stays dark with ink,
oxblood and dusty rose; **Sunday** stays light with linen whites and sage. The console
has the same choices in its header. Choices stay on this browser and origin, work
offline and are separate from shared household data. Original art is unchanged.
See [theme behavior and testing](THEMES.md). Keep your existing volume, port mapping,
command and healthcheck, including `5152:5152`; update only the image reference.
Save edits and accept the PWA update. No browser-data reset or reinstall is required.
