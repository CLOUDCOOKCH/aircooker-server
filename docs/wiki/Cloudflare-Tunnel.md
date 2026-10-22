# Cloudflare Tunnel

Cloudflare Tunnel can expose MealF over HTTPS without forwarding an inbound router port.
The operator runs a `cloudflared` connector separately from the MealF backend. Browser
requests travel through Cloudflare and the connector to the backend's private HTTP listener.
Keep MealF's account authentication enabled.

You need a Cloudflare account, a domain managed in that account, permission to create a
tunnel/public hostname and a Docker host with outbound connectivity to Cloudflare.
Follow Cloudflare's current [connector installation instructions](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/)
for supported platforms and [tunnel firewall requirements](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-with-firewall/).
The connector's outbound tunnel connection is separate from the browser's HTTPS connection.

## Choose where the connector runs

| Connector location | Public hostname's service URL | Backend exposure |
| --- | --- | --- |
| On the Docker host | `http://127.0.0.1:8080` | Supplied loopback-only published port |
| In a separate container | `http://mealf:8080` for preview Compose | Shared private Docker network; no public backend port |

`127.0.0.1` inside a connector container refers to that connector, so it will not reach
MealF. For a source-build deployment the backend service name is `aircooker`, making
the container target `http://aircooker:8080`.

## Create the tunnel and hostname

1. In Cloudflare Zero Trust, open the Cloudflare Tunnels area under Networks/Connectors
   and create a Cloudflared tunnel, for example `mealf`.
2. Choose the host or Docker connector option. Treat the supplied tunnel token as a
   credential. Follow the dashboard's platform installation instructions privately.
3. Add a published application/public hostname such as `meals.example.com`. Choose
   **HTTP** for the service and use the address from the table above. Leave the path
   empty so `/`, `/app/` and `/api/` all reach the same backend.
4. Confirm the dashboard creates the hostname's DNS route. Resolve any existing
   conflicting DNS record instead of creating two competing routes.
5. Set MealF's `BASE_URL` to `https://meals.example.com` and recreate its container.
   For preview Compose, edit `.env`; for source Compose, edit the environment in
   `compose.yaml`. See [Configuration](Configuration).

The public connection uses HTTPS; HTTP is used only for the private connector-to-backend
hop. Keep both on the same host/private Docker network for these examples. Do not disable
TLS verification when configuring a different HTTPS origin service.

## Option A: connector installed on the host

Keep the supplied `127.0.0.1:8080:8080` port binding and configure the tunnel service as
`http://127.0.0.1:8080`. Start the connector using the dashboard's instructions for your
host OS, including its service/start-on-boot option. Tunnel credentials belong to that
host service, not the MealF image or application settings.

Run this on the Docker host to check the private origin before testing the tunnel:

```sh
curl --fail http://127.0.0.1:8080/api/v1/system/health
```

It should return `{"status":"ok"}`. Local HTTP health checks do not establish that
browser login works; test the public HTTPS URL too.

Forwarded-header trust must match the peer seen by the backend. Docker port forwarding
can make a host connector appear as the bridge gateway rather than `127.0.0.1`.
Confirm that address from your network configuration before setting `TRUSTED_PROXY_CIDRS`.
Leave trust empty until verified; never use `*` or trust all networks. Without proxy trust,
client-address rate limits may be shared across tunnel users. Option B provides an explicit
connector address when you want a predictable Docker setup.

## Option B: connector in Docker

This example extends **preview Compose** without changing its existing volume or project
name. For an existing installation, keep using the same installation directory and
`compose.preview.yaml`. Stop any host connector for this tunnel before switching methods.

Add these settings to the private `.env` file alongside your existing `BASE_URL`:

```dotenv
CLOUDFLARED_IMAGE=cloudflare/cloudflared:REPLACE_WITH_REVIEWED_VERSION
CLOUDFLARE_TUNNEL_TOKEN=REPLACE_WITH_YOUR_TUNNEL_TOKEN
```

Replace both placeholders. Select a published cloudflared version supported by Cloudflare,
or pin its immutable image digest. Obtain the token from the tunnel's connector setup
screen, not from a general Cloudflare account API key. Restrict `.env` to the operator
(`chmod 600 .env`) and exclude it from Git and support bundles. Docker administrators can
inspect container environment values; treat them as trusted operators.

Save the following as `compose.tunnel.yaml` next to `compose.preview.yaml`:

```yaml
services:
  mealf:
    environment:
      TRUSTED_PROXY_CIDRS: "172.30.85.2"
    networks:
      tunnel:
        ipv4_address: 172.30.85.3
  cloudflared:
    image: ${CLOUDFLARED_IMAGE:?Set a reviewed cloudflared image}
    restart: unless-stopped
    command: tunnel --no-autoupdate run
    environment:
      TUNNEL_TOKEN: ${CLOUDFLARE_TUNNEL_TOKEN:?Set the tunnel token privately}
    networks:
      tunnel:
        ipv4_address: 172.30.85.2
    read_only: true
    tmpfs:
      - /tmp:size=32m,mode=1777
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    pids_limit: 100
    mem_limit: 128m
networks:
  tunnel:
    ipam:
      config:
        - subnet: 172.30.85.0/24
```

The subnet is an example. Check existing host, VPN and Docker networks first. If it
overlaps, choose an unused private subnet and change the subnet, both service IPs and trusted
proxy address together. Both addresses are fixed to avoid allocation collisions. Trust only
the connector's IP. The network needs outbound access,
so do not mark it `internal: true` without providing another outbound route.

Set the public hostname's service URL to `http://mealf:8080`, then start both services:

```sh
docker compose -f compose.preview.yaml -f compose.tunnel.yaml up -d
docker compose -f compose.preview.yaml -f compose.tunnel.yaml ps
docker compose -f compose.preview.yaml -f compose.tunnel.yaml logs --tail=50 cloudflared
```

Keep both `-f` arguments for future operations on this installation. The original
loopback backend binding remains available for local health checks; the connector
does not need a published port. Do not launch the base Compose file as a second project
against the same data volume. Source-build users can adapt the overlay's `mealf` service
key and tunnel service URL to `aircooker`, retaining their original source Compose volume.

## Cache, access and request settings

- Add a Cloudflare cache rule that **bypasses caching for the MealF hostname**. Do not
  apply a Cache Everything rule to authenticated API, console or media responses.
  The PWA maintains its own browser cache for public application files.
- Keep HTML/JavaScript rewriting, such as Rocket Loader, disabled for this hostname.
  Preserve the backend's content security policy and response headers.
- Preserve the hostname and normal forwarding headers. Do not rewrite requests onto
  another public origin or a path prefix. No WebSocket configuration is required.
- Interactive Cloudflare Access login or WAF challenges can interrupt API requests,
  installed-app use and native clients. Validate those flows before adding an extra
  access layer; MealF does not implement Cloudflare service-token authentication.
- Cloudflare plan limits may reject uploads below MealF's 280 MiB archive allowance.
  For large restores, use an HTTPS ingress that supports the required size, or a
  supported smaller transfer. Never expose an unauthenticated restore route.

## Verify the installation

Open `https://meals.example.com/api/v1/system/health`, then `/` and `/app/`. Complete
[First-run setup](First-Run-Setup), sign in, save a test recipe and reload. Confirm the
tunnel remains connected after restarting the connector. An HTTP health response alone
does not verify cookies, CSRF, uploads or PWA installation.

A Cloudflare 502 usually means the connector cannot reach the configured private origin.
Check the service name, network, port and backend health. A tunnel unavailable/1033 error
points to connector availability or routing. A browser 403 after the page loads usually
needs an exact `BASE_URL`, cookie/CSRF or edge-policy check. See [Troubleshooting](Troubleshooting).

This is a documented deployment pattern; no live Cloudflare account/tunnel was exercised
while preparing these guides.

Source: [deployment](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/DEPLOYMENT.md)
and [Cloudflare's remotely managed tunnel guide](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/).
