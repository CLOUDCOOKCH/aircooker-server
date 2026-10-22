# mealf identity and compatibility

The confirmed product name is **Mealf** (2026-10-21). Both original PNGs were
received in `mealf-flirty-peach-wortmarke.zip`. The PWA and administration console now use
the supplied peach and lowercase image wordmark instead of the interim utensil/text mark.
Keep the approved glass interface, system typography, system appearance and accessible flows. The user-approved palette refresh below supersedes the earlier green-control constraint.

Both supplied files remain byte-for-byte intact in `assets/brand/originals/`:

| File | Original size | SHA-256 |
| --- | --- | --- |
| mealf-flirty-peach-logo.png | 1254 × 1254 RGBA | a3384ae38b80af70aa63400af2f8fc1525e4e5a11370daca3ffc67d0c82aa69e |
| mealf-flirty-peach-wortmarke.png | 1774 × 887 RGBA | dfbba3ebedca96dbc76d7baef7bafad75228f0c90ffdafde234c2ccc02b9d3fb |

`scripts/build_brand_assets.py` trims only fully transparent outer space, proportionally
resizes and centres the original pixels. Installation icons have an opaque cream canvas;
the maskable variant fits inside the central safe circle. No artwork is redrawn, recoloured,
traced or regenerated. The original files stay outside the public bundle and worker cache.
`frontend/public/brand/provenance.json` records source/derived hashes and trim bounds.
Run `.venv/bin/python scripts/build_brand_assets.py --check` to verify them. CI checks
against the originals; Docker E2E checks the bytes actually served by the packaged image.

The PWA, console, English/German onboarding, browser title, manifest names, dependency
notices, download filenames and native app/extension display copy use mealf. Household
names chosen by users are preserved. The PWA manifest's `/app/` identity/start URL stays
stable. The welcome/header, boot state, desktop navigation, footer and console use the
actual wordmark and peach. Wordmark images expose the accessible name mealf; adjacent peach
images have empty alt text inside localized native slap buttons (the boot image remains
decorative). Wordmark links remain separate. See [interaction behavior](PEACH_EGG.md). Favicon, 180px Apple touch icon, 192/512px manifest icons and a
separate maskable icon use the peach. Old icon URLs also resolve to the new artwork.

Versioned filenames refresh icon metadata. The worker precaches the public assets and its
content hash changes; use the existing explicit application-update flow after finishing
an active edit. Browser data does not need resetting. An OS may cache an installed icon
longer than the page; real iPhone icon refresh remains unverified. Do not clear storage or
remove an installed app with unsynchronised work merely to refresh its icon. Protect/sync
local work first. The retained native repository's artwork is not changed by this PWA release.

Current source, package, native target and operator names use Mealf. The administration
console lives at `/admin/`; the root path is reserved for the separate landing page.
Read [the upgrade guide](MEALF_MIGRATION.md) for SQLite migration, browser/session/archive
compatibility, the preserved `/app/` identity and valid existing repository URLs.
Historical validation records and original asset provenance retain their tested hashes.

## Approved web palette and voice refresh — 2026-10-21

The user explicitly requested the Mealf design throughout the PWA and administration console. Light appearance uses cream, coral and peach; dark appearance uses cocoa and peach. Raspberry danger roles remain distinct. The shared semantic `--accent*` tokens replace the former green-named roles. `frontend/src/tokens.css` is authoritative; the build exports its exact bytes as `/app/theme.css`, imported by the console. See [the exact two-theme design snapshot](../DESIGN.md) and [admin brief](../.impeccable/surfaces/admin.md).

English/German food innuendo is approved for welcome/login, empty-state, sidebar and footer copy, including a playful login headliner. Setup instructions, help, consent/security, errors and recovery remain literal. Preserve solid forms, system headings, the glass navigation material, original artwork bytes and the compatibility rules in the upgrade guide. Native changes are deferred.

Current genuine [PWA welcome](screenshots/mealf-palette-pwa-welcome-desktop.png), [dark phone welcome](screenshots/mealf-palette-pwa-welcome-phone-dark.png), [console login](screenshots/mealf-palette-admin-login-desktop.png) and [dark console](screenshots/mealf-palette-admin-desktop-dark.png) captures record the implemented web direction. Historical artwork/name/green-palette reviews and published preview evidence retain their original scope. Local automated/browser checks passed as recorded in [IMPLEMENTATION.md](IMPLEMENTATION.md); the [manual palette finish review](validation/mealf-palette-review.md) records **ship within the reviewed palette, administration and copy scope**, with zero required material findings. Publication is verified in `poc-20261021.5`; see the combined release evidence in `docs/validation/github-preview-retry.json`. No physical iPhone/live-service or unavailable detector/schema validation is claimed.
