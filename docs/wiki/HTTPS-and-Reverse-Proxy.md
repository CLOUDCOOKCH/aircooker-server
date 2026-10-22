# HTTPS and reverse proxy

MealF needs a valid HTTPS origin for browser authentication and PWA installation.
Set `BASE_URL` to that exact origin, for example `https://meals.example.com`, without
`/app/` or another path. A non-default HTTPS port, if used, is part of the origin.
Serve the console, PWA and API on that same origin.

Use [Cloudflare Tunnel](Cloudflare-Tunnel) or your own HTTPS reverse proxy. The supplied
Compose files bind backend port 8080 only on host loopback. Do not publish it directly
to the internet. Keep normal certificate verification enabled.

## Host-installed Caddy example

Point your hostname's DNS at the reverse proxy and arrange certificate issuance using
your chosen Caddy deployment. Install a current supported Caddy version. The backend
should be reachable from that host at `127.0.0.1:8080`.

```caddy
meals.example.com {
    @archive path /api/v1/admin/import/archive
    request_body @archive {
        max_size 280MiB
    }
    @jsonRestore path /api/v1/admin/import
    request_body @jsonRestore {
        max_size 8MiB
    }
    @uploads path /api/v1/media/* /api/v1/import-sources/*
    request_body @uploads {
        max_size 9MiB
    }
    @ordinary not path /api/v1/admin/import/archive /api/v1/admin/import /api/v1/media/* /api/v1/import-sources/*
    request_body @ordinary {
        max_size 1500000
    }
    reverse_proxy 127.0.0.1:8080
}
```

Replace the hostname, validate the Caddy configuration and reload using your host's
service-management procedure. If the reverse proxy is another container, place both
services on an appropriate private network and use `mealf:8080`. Its own `127.0.0.1` will not reach the backend container.

The import-source route is available only in images containing the AI media-import
feature. Keeping its ingress allowance does not enable a missing backend feature.

## Forwarded headers and proxy trust

Have the proxy preserve the public host and forward the original scheme and client IP.
Set `TRUSTED_PROXY_CIDRS` to only the actual proxy peer address(es) or controlled proxy
range seen by Uvicorn. An empty value is the default. Never use `*` on public ingress.
Host-to-container traffic can appear as a Docker bridge gateway; do not assume that a
host-installed proxy appears as loopback inside the container.

For a container proxy, a fixed address on a dedicated network provides a predictable
peer. The [Cloudflare Docker example](Cloudflare-Tunnel#option-b-connector-in-docker)
shows this pattern. Do not trust an entire LAN or all private networks merely to make
forwarding work. Recreate the backend after changing its environment.

## Request limits

| Request | Backend limit | Proxy allowance in the example |
| --- | --- | --- |
| Ordinary JSON/API writes | 1,500,000 bytes | 1,500,000 bytes |
| Recipe photos and AI source uploads | 8 MiB source, with bounded request overhead | 9 MiB |
| Household JSON import | 8 MiB | 8 MiB |
| Household ZIP import | 280 MiB | 280 MiB |

Keep limits specific to their routes. Increasing the proxy allowance does not raise
the application's own limit. Add suitable read timeouts and ingress rate limits for
your host; an AI call can take up to its configured timeout. There is no required
WebSocket or streaming ingress. An external CDN may impose a lower upload ceiling.

## Verify browser access

1. Visit `/api/v1/system/health` on the public HTTPS hostname.
2. Visit `/admin/` and `/app/` and sign in using that same hostname.
3. Save a test recipe and check that it survives reload.
4. If you will use them, test image upload and a private export/import in your environment.

Session cookies are always Secure, HttpOnly and SameSite=Strict. Unsafe cookie requests
also need the configured Origin and CSRF token. Do not strip cookies or Origin headers,
split the API onto a second hostname, or disable these checks to fix login. See
[Troubleshooting](Troubleshooting) for 401/403 and certificate errors.

Source: [deployment](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/DEPLOYMENT.md)
and [security model](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/SECURITY_MODEL.md).

For a separately hosted root landing page, keep the backend prefixes intact and use
[Mealf path routing](../MEALF_MIGRATION.md#landing-page-and-reverse-proxy).
