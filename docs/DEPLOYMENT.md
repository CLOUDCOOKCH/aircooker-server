# Deployment and upgrades

This development image is not yet a production release. All examples require review of
`IMPLEMENTATION.md` and an HTTPS ingress. One container contains API, console, worker and DB.

For step-by-step instructions, see the [Wiki installation guide](wiki/Installation.md),
[Cloudflare Tunnel guide](wiki/Cloudflare-Tunnel.md) and [complete guide index](WIKI.md).

## Build and first run

Use Docker Engine with Compose v2 and a local filesystem-backed named volume:

```sh
docker compose up --build -d
docker compose logs aircooker
```

Set `BASE_URL` in Compose to the external HTTPS origin. Open that origin, enter the one-time
token and create the household. Copy `setup_token` from the startup log entry with event
`setup_required`; a container manager's Logs view works without opening a terminal.
The token is generated from 48 random bytes and also stored in the protected data directory.
It is logged once per server startup while unconfigured, including on upgrades/restarts that
retain an existing token. Setup is transactional and locks after one household. Configured
starts do not log a token. Old log records remain subject to the container log retention
policy, but their token cannot be reused after setup. Keep container logs operator-only;
`LOG_SETUP_TOKEN=false` disables this bootstrap-only disclosure.
Use `docker compose exec -it aircooker python -m aircooker.cli recover` for local administrator
password recovery. It revokes all sessions; no public recovery/reset endpoint exists.

For a NAS/container-manager console, use `/bin/bash` (included since POC `.2`) or `/bin/sh`,
then run `cat /data/config/setup-token`. Never paste the token into support issues. Earlier
POC `.1` has only `/bin/sh`; update the image while retaining the existing volume if your
terminal client requires Bash. No host root access or extra container privileges are needed.

UID/GID 10001 needs write access to `/data`. A new named volume gets the image's data-directory
ownership. For a bind mount, create/chown that directory explicitly. Never give the container
a Docker socket, privileged mode, or host filesystem access. The application filesystem can
be read-only; `/tmp` is a bounded tmpfs. Keep the single-worker process model.

| Variable | Default | Behaviour |
| --- | --- | --- |
| DATA_DIR | /data | Local persistent state; never use a live SQLite database on NFS/SMB |
| DATABASE_MAX_BYTES | 2147483648 | SQLite main-file growth cap (2 GiB); integer from 1 MiB to 64 GiB, applied on every connection |
| BASE_URL | https://localhost | Exact allowed browser origin; no trailing application path |
| LOG_LEVEL | info | Uvicorn level; keep third-party debug logging disabled |
| LOG_SETUP_TOKEN | true | Print the one-time setup token at unconfigured startup; false disables it, with file access retained |
| TRUSTED_PROXY_CIDRS | empty | Uvicorn trusted proxy addresses/CIDRs; never `*` on public ingress |
| TZ | image setting | Process time zone only; household IANA zone controls planning |
| AI_PROVIDER | unset | Optional gemini/openai/openrouter/openai-compatible/anthropic/ollama/openwebui |
| AI_BASE_URL | provider default | Administrator-selected API base; imported content cannot change it |
| AI_MODEL | unset | Required when configuring AI; no guessed model name |
| AI_API_KEY_FILE | unset | Restricted regular file, no group/world access, not a symlink |
| AI_INPUT_FORMATS | text | Comma-separated model capabilities, e.g. `text,image,pdf`; supported formats depend on provider |
| AI_TIMEOUT | 30 | 1–120 seconds |
| AI_MAX_CONTENT | 50000 | 100–100000 UTF-8 bytes |
| AI_REQUESTS_PER_HOUR | 20 | Shared durable hourly budget for AI imports and connection probes |
| AI_STRUCTURED_OUTPUT | 0 | Opt into provider-specific JSON mode after compatibility verification |
| AI_ALLOW_LOCAL_HTTP | 0 | Explicitly permit the configured local provider's HTTP endpoint |

Console-saved encrypted AI settings override these AI environment values, including when
AI is disabled in the console. See [administration](ADMINISTRATION.md).

Persistent layout: `database/aircooker.sqlite3` (+ WAL/SHM), `media/`, `jobs/`, `backups/`,
`config/setup-token`, `config/integrations.key`, encrypted integration files and optional
Bring compatibility report. Queue records currently live in SQLite, not job files.

## HTTPS reverse proxy

Bind the application only to loopback as in Compose, or use an isolated Docker network.
Terminate public TLS using a valid certificate. Set request read timeouts and ingress rate
limits. Ordinary JSON requests are bounded to 1,500,000 bytes by the application; photos
allow 8 MiB plus multipart overhead, JSON restores 8 MiB and ZIP restores 280 MiB. Configure
matching route-specific ingress limits so large restores do not increase ordinary API limits. Do not expose 8080 directly to the internet.
Configure only the actual proxy address/range in `TRUSTED_PROXY_CIDRS`; forward original
host, client IP and scheme. Cookie authentication always uses Secure/HttpOnly/SameSite=Strict
and also requires CSRF header and the exact `BASE_URL` Origin on unsafe requests.

Example Caddy configuration for a host-installed reverse proxy:

```caddy
meals.example.com {
    @archive path /api/v1/admin/import/archive
    request_body @archive { max_size 280MiB }
    @jsonRestore path /api/v1/admin/import
    request_body @jsonRestore { max_size 8MiB }
    @media path /api/v1/media/* /api/v1/import-sources/*
    request_body @media { max_size 9MiB }
    @ordinary not path /api/v1/admin/import/archive /api/v1/admin/import /api/v1/media/* /api/v1/import-sources/*
    request_body @ordinary { max_size 1500000 }
    reverse_proxy 127.0.0.1:8080
}
```

If both are containers, use a private network and the service name instead of loopback.
Do not configure an arbitrary CIDR merely to make forwarded headers work. Health checks use
plain HTTP only inside the container; iOS and browser ingress must use HTTPS. No WebSocket
or streaming ingress is required.

## Cloudflare Tunnel

Run cloudflared as an operator-managed ingress, outside the mandatory backend container.
Map the public hostname to `http://127.0.0.1:8080` for a host tunnel, or an isolated service
address for a container tunnel. Match `BASE_URL` to the public HTTPS origin. Restrict the
origin listener, trust only the tunnel process/network and keep application authentication
enabled. Tunnel credentials are never part of the aircooker image. An interactive Cloudflare
Access login may block the native client; do not assume an Access-protected origin works
with a plain URLSession client.

## Upgrade and rollback

Before an upgrade, create and verify an encrypted volume/SQLite backup. Pin an immutable
image digest or release tag once releases exist. Stop the old container, keep its data
volume, start the new image and inspect readiness/migration health. A failed migration
rolls back its transaction. Downgrading a migrated database is not supported: restore the
matching pre-upgrade volume snapshot with the prior image. Never delete a volume to upgrade.

## Troubleshooting

401: reauthenticate; refresh replay intentionally revokes a session. 403 in browser: check
HTTPS, exact BASE_URL/Origin and CSRF cookie/header. iOS TLS failure: fix the certificate
chain and DNS, never add an arbitrary insecure exception. Setup locked: use the existing
account or local recovery. 429: wait for the durable rate-limit bucket to expire.
Bring capability unverified: run the dedicated-list compatibility probe. Import needs-input:
retain the URL and provide a structured recipe or manually enter the missing content.

## Routine maintenance

Bounded hourly SQLite retention and startup-only stale transfer cleanup run inside this
container. Inspect candidates with `docker compose exec aircooker python -m aircooker.cli
cleanup --dry-run`; apply an extra pass by omitting `--dry-run`. Output contains counts only.
Offline sync/Bring replay history and uploaded images remain protected. See RETENTION.md
for windows, upgrade grace, failure logs and remaining compaction limits.
