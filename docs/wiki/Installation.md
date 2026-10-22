# Installation

MealF runs on Docker hosts supporting `linux/amd64` or `linux/arm64`. The backend
container includes the PWA, administration console, API and background worker.
Use Docker Engine with Compose v2 and a local filesystem for SQLite. Do not place
the live database on an NFS or SMB share.

## Install a prebuilt preview

1. Create a directory for the installation.
2. Download `compose.preview.yaml` from your chosen
   [GitHub prerelease](https://github.com/CLOUDCOOKCH/aircooker-server/releases).
   Keep the Compose file and image from the same release together.
3. Create a private `.env` file beside it:

   ```dotenv
   BASE_URL=https://meals.example.com
   TZ=Europe/Zurich
   ```

   Replace the hostname with your actual public HTTPS origin. Do not append `/app/`.
   On Unix, restrict the file with `chmod 600 .env`. Do not commit private configuration.
4. Configure [Cloudflare Tunnel](Cloudflare-Tunnel) or an
   [HTTPS reverse proxy](HTTPS-and-Reverse-Proxy) on that hostname.
5. Start the backend from the installation directory:

   ```sh
   docker compose -f compose.preview.yaml pull
   docker compose -f compose.preview.yaml up -d
   docker compose -f compose.preview.yaml ps
   docker compose -f compose.preview.yaml logs --tail=100 mealf
   ```

Use the setup token in the private startup log to complete [First-run setup](First-Run-Setup).
Open `https://meals.example.com/app/` to use the PWA.

The Compose file pins a preview image tag. To select another reviewed image, set
`MEALF_IMAGE` in `.env` to its release tag or immutable manifest digest. Obtain the
actual digest from the release; do not copy a placeholder. The moving `:preview`
channel is for deliberate preview updates. There is no implied stable release.
Features added after your release require a newer published image or a source build.

## Build from source

Use this route when you need changes that have not been included in a published image:

```sh
git clone https://github.com/CLOUDCOOKCH/aircooker-server.git mealf-server
cd mealf-server
```

Check out the source revision you intend to run. Edit `compose.yaml` to set the
external HTTPS `BASE_URL`, process time zone and any confirmed proxy trust addresses.
This file has literal environment values: adding `BASE_URL` to `.env` alone does
not override them. Then run:

```sh
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 mealf
```

Docker builds the frontend automatically; Node is not a separate running service.
The Compose project names differ between source and preview deployments.
The two Compose files create different named volumes. Do not switch between them
expecting existing data to move automatically. See [Backup and recovery](Backup-and-Recovery).

## Storage and container settings

The supplied files bind port 8080 only to `127.0.0.1` on the host. Keep that restriction
when using a host ingress. A connector in another container reaches the backend by
service name on a private Docker network, as shown in [Cloudflare Tunnel](Cloudflare-Tunnel).
Public browser access must use HTTPS.

Keep the named volume mounted at `/data`. For a bind mount, create a dedicated local
directory and give UID/GID **10001:10001** write access. Keep the supplied non-root,
read-only filesystem, bounded `/tmp`, dropped capabilities and single-process command.
Do not add a Docker socket, privileged mode or extra backend replicas.

On a NAS/container manager, preserve these same image, environment, port and volume
settings. Its Logs view can display the bootstrap token; its terminal can use
`/bin/bash` or `/bin/sh` in current previews. Host root access is not needed to read
the token through the container terminal. Keep that terminal and log access private.

Never remove the data volume to update the application. In particular,
`docker compose down -v` deletes named-volume data. Back up first and follow
[Upgrades and maintenance](Upgrades-and-Maintenance).

Source: [deployment](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/DEPLOYMENT.md),
[preview guide](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/POC.md),
[preview Compose](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/compose.preview.yaml).
