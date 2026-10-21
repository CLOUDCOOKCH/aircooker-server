# Deployment and upgrades

This development image is not yet a production release. All examples require review of
`IMPLEMENTATION.md` and an HTTPS ingress. One container contains API, console, worker and DB.

## Build and first run

Use Docker Engine with Compose v2 and a local filesystem-backed named volume:

```sh
docker compose up --build -d
docker compose exec aircooker cat /data/config/setup-token
```

Set `BASE_URL` in Compose to the external HTTPS origin. Open that origin, enter the one-time
token and create the household. The token is a random 48-byte URL-safe secret readable only
from the protected data directory. Setup is transactional and locks after one household.
Use `docker compose exec -it aircooker python -m aircooker.cli recover` for local administrator
password recovery. It revokes all sessions; no public recovery/reset endpoint exists.

UID/GID 10001 needs write access to `/data`. A new named volume gets the image's data-directory
ownership. For a bind mount, create/chown that directory explicitly. Never give the container
a Docker socket, privileged mode, or host filesystem access. The application filesystem can
be read-only; `/tmp` is a bounded tmpfs. Keep the single-worker process model.

| Variable | Default | Behaviour |
| --- | --- | --- |
| DATA_DIR | /data | Local persistent state; never use a live SQLite database on NFS/SMB |
| BASE_URL | https://localhost | Exact allowed browser origin; no trailing application path |
| LOG_LEVEL | info | Uvicorn level; keep third-party debug logging disabled |
| TRUSTED_PROXY_CIDRS | empty | Uvicorn trusted proxy addresses/CIDRs; never `*` on public ingress |
| TZ | image setting | Process time zone only; household IANA zone controls planning |
| AI_PROVIDER | unset | Optional openai/openai-compatible/anthropic/ollama/openwebui |
| AI_BASE_URL | provider default | Administrator-selected API base; imported content cannot change it |
| AI_MODEL | unset | Required when configuring AI; no guessed model name |
| AI_API_KEY_FILE | unset | Restricted regular file, no group/world access, not a symlink |
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
    @media path /api/v1/media/*
    request_body @media { max_size 9MiB }
    @ordinary not path /api/v1/admin/import/archive /api/v1/admin/import /api/v1/media/*
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
