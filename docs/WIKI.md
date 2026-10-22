# Wiki guide sources

These pages are maintained in `docs/wiki/` for later publication in the
[GitHub Wiki](https://github.com/CLOUDCOOKCH/aircooker-server/wiki). Adding them to this
repository does not publish the separate Wiki or a container release.

| Guide | Contents |
| --- | --- |
| [Home](wiki/Home.md) | Overview, recommended reading order and current limits |
| [Installation](wiki/Installation.md) | Docker preview, source build, NAS and persistent storage |
| [First-run setup](wiki/First-Run-Setup.md) | Setup token, household account, time zone and password recovery |
| [Cloudflare Tunnel](wiki/Cloudflare-Tunnel.md) | Public hostname, host connector and Docker connector configuration |
| [HTTPS and reverse proxy](wiki/HTTPS-and-Reverse-Proxy.md) | Caddy, origin matching, proxy trust and upload limits |
| [Configuration](wiki/Configuration.md) | Environment settings, configuration precedence and data paths |
| [PWA and offline use](wiki/PWA-and-Offline-Use.md) | Installation, offline edits, synchronisation and recovery |
| [Backup and recovery](wiki/Backup-and-Recovery.md) | Portable exports, SQLite snapshots and complete volume recovery |
| [Upgrades and maintenance](wiki/Upgrades-and-Maintenance.md) | Image updates, rollback, health checks and retention |
| [AI recipe import](wiki/AI-Recipe-Import.md) | Providers, credentials, supported formats and reviewed imports |
| [Personal ChatGPT connection](CHATGPT.md) | Windows helper, personal plan usage and reviewed text imports |
| [Bring! integration](wiki/Bring-Integration.md) | Connection, list selection, compatibility probe and shopping behaviour |
| [Meal reminders](wiki/Meal-Reminders.md) | Optional Web Push, device setup, privacy and delivery limits |
| [Troubleshooting](wiki/Troubleshooting.md) | Installation, login, tunnel, import and sync problems |

## Editing and publishing

Wiki pages use extensionless links such as `[Installation](Installation)` so they work
after publication. Use the table above to browse the source files in this repository.
Links to code, release information and engineering documents are absolute repository URLs.
`Home.md` is the Wiki landing page; `_Sidebar.md` supplies navigation on every page.

To publish, a repository maintainer must first enable the Wiki in GitHub settings and
create its initial page if necessary. Clone `aircooker-server.wiki.git` separately,
copy the Markdown files from `docs/wiki/` into its root, inspect the diff, then commit
and push that Wiki repository. Preserve any existing Wiki pages that are not represented
here; do not delete them automatically. Only copy `docs/wiki/*.md`, not this source index,
private configuration, screenshots containing secrets or local build output.

Keep commands consistent with `compose.preview.yaml` and `compose.yaml`. The preview
service is `mealf`; the source-build service is `aircooker`. Distinguish source-only
features from published image capabilities and retain explicit unverified limitations.

[Shopping requirements and manual Bring! sync](SHOPPING.md) explains item states, offline snapshots and the packaged compatibility check.
