# Mealf names and administration paths

## Routes

- `/admin/`: administration, login and first-run setup. `/admin` redirects here.
- `/admin/console.js` and `/admin/console.css`: console assets.
- `/app/`: the installable meal planner, with its existing manifest identity and worker scope.
- `/api/v1/`: the unchanged versioned API and authenticated administration operations.
- `/`: reserved for the operator's landing page; the backend returns 404 without redirecting.

The console shares brand, theme and peach assets under `/app/`. Keep all three backend
prefixes on the same HTTPS origin. `BASE_URL` remains the origin, without `/admin/` or
`/app/`. The landing page is supplied separately; this release does not create one.

## Existing installations

Back up the data volume before upgrading. Stop the old container, retain the **same volume,
Compose project/service mapping, public origin and 5152:5152 port configuration**, and
start the new image. Do not delete the volume, clear browser storage or reinstall the PWA.

New Python installations use `mealf-server` and `python -m mealf`. A custom internal
5152 command can now use:

```yaml
command: [python, -m, uvicorn, 'mealf.app:create_app', --factory, --host, 0.0.0.0, --port, '5152']
ports: ['5152:5152']
healthcheck:
  test: [CMD, python, -c, "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5152/api/v1/system/health', timeout=3)"]
```

Preserve existing trusted-proxy options on custom commands. Without a custom command,
the image and example Compose continue to use internal port 8080. A deprecated command
shim also accepts the old module path, so an image-only update does not break an existing
5152 deployment. Fresh configuration and documentation use Mealf exclusively.

At startup, under the existing single-instance volume lock, the server checkpoints the
previous SQLite WAL before publishing `database/mealf.sqlite3`. It does not create another
household or rewrite sync IDs, media, queued jobs, session tokens, integration secrets or
Bring! ownership. An interrupted link publication is resumable. If two different database
files exist or the WAL cannot be checkpointed, startup fails rather than choosing one or
discarding data. Stop every other database reader/writer before upgrading. Rolling back
requires the prior image and matching pre-upgrade volume snapshot.

Existing browser sessions and CSRF cookies remain readable. Login/refresh writes current
Mealf cookie names and expires legacy cookies; logout clears both. Import confirmation
accepts previous sync-header names during compatibility upgrades, rejects conflicting
alias values, and advertises only current names in OpenAPI. Password hashing, session
revocation, CSRF, exact-origin checks and cookie security attributes remain enforced.

New browser databases use `mealf:<instance-id>`. Existing installations continue using
their physical database in place: recipes, photos, drafts, queued image imports, recovery
archives, stable mutation/device IDs and unsent edits are not copied or deleted. Cross-tab
channels and Web Locks follow the selected database namespace so older tabs still
coordinate. If both old and new databases exist, the app refuses to select one; protect
both browser databases and seek recovery rather than clearing storage. Connection metadata
and the current worker cache use Mealf names; activation recognizes and cleans old shell
caches while leaving unrelated landing-page caches alone.

New household JSON/ZIP exports and browser recovery downloads use Mealf format names.
Previous household export formats remain accepted, including images. Export versions and
the API/sync major versions have not changed.

## Landing page and reverse proxy

Route the exact `/admin` path and `/admin/*`, `/app/*` and `/api/v1/*` to the backend
**without stripping their prefixes**. Serve the remaining paths from your landing host.
For example, inside the Caddy site block from [Deployment](DEPLOYMENT.md), replace its
catch-all `reverse_proxy` with:

```caddy
@mealf path /admin /admin/* /app /app/* /api/v1 /api/v1/*
handle @mealf {
    reverse_proxy 127.0.0.1:5152
}
handle {
    root * /srv/mealf-landing
    file_server
}
```

Use your actual private backend address/port and landing deployment. Retain the documented
route-specific upload limits, valid TLS and trusted proxy settings. A Cloudflare Tunnel
can point at this path-routing reverse proxy; a hostname mapped directly to the backend
will return the backend's 404 at `/` until the landing route is configured.

## Repository and native development names

Active Python modules, Swift package/module/targets, build scripts, current contracts and
operator examples use Mealf. The retained native app uses `ch.cloudcook.mealf`, matching
App Groups and the `mealf` scheme. It has not been distributed on the App Store: native
developers must provision the new identifiers and install a fresh development build.
Migration across Apple's application sandboxes is not claimed. PWA storage is unaffected.

The actual GitHub repositories still have their existing URLs until the owner renames
them in GitHub **Settings → General → Repository name**. This environment cannot rename
GitHub repositories. Links and the contract pin retain the valid URLs; no nonexistent
remote is advertised. Historical release/test evidence, Git history and released
migrations retain their original names and hashes. Compatibility identifiers occur only
where needed to read existing installations or archives.
