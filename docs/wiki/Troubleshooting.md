# Troubleshooting

Start with the exact image/source revision, backend health and the affected URL. Use
the same Compose files and project name as your installation. Preview service name is
`mealf`; source-build service name is `aircooker`.

## Basic checks

For preview Compose with a host ingress:

```sh
docker compose -f compose.preview.yaml ps
curl --fail http://127.0.0.1:8080/api/v1/system/health
curl --fail https://meals.example.com/api/v1/system/health
```

Replace the hostname. If using the Docker tunnel overlay, add
`-f compose.tunnel.yaml` to Compose commands. Private HTTP health checks do not verify
public cookies, CSRF, PWA installation or external integrations.

Read private logs locally when needed:

```sh
docker compose -f compose.preview.yaml logs --tail=100 mealf
```

Unconfigured startup logs contain the one-time setup token by default. Redact it before
sharing any log excerpt. Use administration Overview for bounded job states/error codes;
do not upload a database, `.env` file or complete Compose configuration containing secrets.

## Installation, setup and login

| Symptom | Check / action |
| --- | --- |
| Backend stops or cannot write `/data` | Verify volume mount, free space and UID/GID 10001 ownership; retain the single backend process |
| Unhealthy after upgrade | Inspect migration errors privately; preserve the volume and use the matching backup/image for rollback |
| Setup appears after an upgrade | Stop and check the original volume/project mapping before creating another household |
| Setup token missing | Check private unconfigured startup logs or `/data/config/setup-token`; configured households use sign-in/local recovery |
| Setup is locked | The household exists; use its credentials or interactive local password recovery |
| Browser 401 / session expired | Sign in again; the console's access session is short-lived, and password changes/recovery revoke sessions |
| Browser 403 after the page loads | Verify valid HTTPS, exact `BASE_URL` including any port, same-origin API use and cookie/CSRF handling |
| Environment edit has no effect | Recreate with `up -d`; `restart` retains the old environment; `.env` values must be referenced by Compose |
| Certificate failure | Fix DNS, hostname and certificate chain; do not disable certificate verification |
| HTTP 429 | Wait for the application/provider rate-limit window and inspect configured quotas; avoid repeated retries |

See [First-run setup](First-Run-Setup), [Configuration](Configuration) and
[Upgrades and maintenance](Upgrades-and-Maintenance).

## Cloudflare and reverse proxy

| Symptom | Check / action |
| --- | --- |
| Cloudflare 502 | Test the private backend; check tunnel service URL, Docker network and port |
| Tunnel unavailable / 1033 | Check connector health, token, outbound firewall connectivity and hostname route |
| Connector in Docker cannot reach `127.0.0.1:8080` | Use `http://mealf:8080` on the shared network, or `aircooker` for source Compose |
| All clients share address-based limits | Confirm proxy peer/header trust; do not set universal trusted proxies |
| HTML loads but API calls return a login/challenge page | Inspect Cloudflare Access/WAF policy and ensure legitimate app/API requests can complete |
| Private or stale content appears through the edge | Bypass cache for the MealF hostname and remove conflicting Cache Everything/rewriting rules |
| HTTP 413 / large restore rejected | Check both application route limits and the proxy/Cloudflare plan ceiling; ZIP allows up to 280 MiB in the backend |

See [Cloudflare Tunnel](Cloudflare-Tunnel) and [HTTPS and reverse proxy](HTTPS-and-Reverse-Proxy).

## PWA, offline data and synchronisation

| Symptom | Check / action |
| --- | --- |
| Install option missing | Open `/app/` on valid HTTPS in a supported browser; on iPhone use Safari → Add to Home Screen |
| Old PWA after image update | Finish edits, accept the update prompt and reopen; do not clear pending local work |
| A photo is unavailable offline | It may not have been viewed/cached before disconnection |
| Pending work will not sync | Sign in, return to foreground and inspect rejected work; export unsynchronised work before recovery |
| Server history changed after restore | Preserve local exports and use explicit history recovery; old queues must not drain blindly |
| Browser data disappeared | Storage may have been evicted/cleared; restore only from surviving server/device exports and backups |

Signing out does not erase cached work, but clearing site data or uninstalling may.
Browser recovery JSON is for inspection/manual reconstruction and is different from
the server's importable household JSON/ZIP. See [PWA and offline use](PWA-and-Offline-Use).

## Imports, Bring! and reminders

| Symptom | Check / action |
| --- | --- |
| AI media controls are missing | Check whether your deployed image includes the source feature; a Wiki page does not update an image |
| AI says not configured despite environment values | A saved disabled/profile setting overrides AI environment settings |
| Unsupported AI input format | Enable it only for a model/API that supports that exact input contract |
| AI key rejected or model not found | Verify provider, endpoint, exact model ID, account access, API billing and key restrictions |
| AI configuration changed during a queued import | Review the new destination/model and give renewed consent |
| Import needs input / invalid extraction | Correct missing facts manually; private sources and unsupported social captions are not bypassed |
| Bring! login works but writes stay disabled | Check the genuine current compatibility report matching SDK and selected test list |
| Reconciliation is queued but list unchanged | Inspect completed/failed job status and ownership/pantry/week rules; queuing is not an external-write receipt |
| Reminder accepted but absent on device | Check permission, installed-app support, Focus/connectivity, time zone and expiry; acceptance is not display proof |
| Importing a household export returns 409 | Duplicate entity IDs reject the merge; destructive replacement is unsupported |

See [AI recipe import](AI-Recipe-Import), [Bring! integration](Bring-Integration),
[Meal reminders](Meal-Reminders) and [Backup and recovery](Backup-and-Recovery).

## Information to include in an issue

Share the image tag/digest or source commit, CPU architecture, browser/OS version,
redacted error code, approximate time and minimal reproduction steps with synthetic
data. State whether private/public health works and whether it is a host or Docker
connector. Exclude household recipes, credentials, tunnel tokens, cookies, signed URLs,
setup tokens and private exports. Clearly distinguish synthetic validation from a live
provider/device result.

Source: [deployment](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/DEPLOYMENT.md),
[administration](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/ADMINISTRATION.md)
and the feature-specific guides linked above.
