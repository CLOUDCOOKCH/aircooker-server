# First-run setup

Before creating an account, start the backend, configure HTTPS and set `BASE_URL`
to the exact public origin, such as `https://meals.example.com`. The console at `/admin/`
and the PWA at `/app/` share that origin. See [Installation](Installation).

## Find the one-time setup token

While no household exists, each backend startup writes a `setup_required` log entry
with `setup_token`. Read it in your container manager's private Logs view, or use:

```sh
docker compose -f compose.preview.yaml logs --tail=100 mealf
```

Alternatively, read the restricted file from the running container:

```sh
docker compose -f compose.preview.yaml exec mealf cat /data/config/setup-token
```

For a source build, use `docker compose logs mealf` and
`docker compose exec mealf cat /data/config/setup-token`. Do not paste the token
or unredacted startup logs into support issues. Set `LOG_SETUP_TOKEN=false` in the
backend's Compose environment if you prefer file-only retrieval, then recreate the
container. The token remains available in the file until successful setup.

## Create the household

1. Open `/admin/` on the public HTTPS origin in your browser. You can also choose **Open your kitchen**
   from the PWA onboarding screen.
2. Enter the setup token.
3. Choose your own username and password. The password must contain at least 12 characters.
   There is no default account.
4. Enter a household name and an IANA time zone, for example `Europe/Zurich` or
   `Europe/Berlin`. Choose the household language where offered.
5. Complete setup, sign in and open `/app/`.

Setup creates one household transactionally and then locks. The setup-token file is
removed and the token cannot be reused. Configured starts stop logging it, although
historical log records remain. Public registration is not available after setup.

## Review the initial settings

At `/`, open **Household** to verify the name, time zone and default language.
The household time zone controls meal dates, shopping-week boundaries and reminder
times. The container's `TZ` variable does not replace it. Changing the displayed
English/German UI language is separate from saving the household default.

Open **Account** to review device sessions. The shared account has household-wide
access; there are no separate administrator roles. Each device/browser has its own
revocable session. Changing the password revokes all sessions, including your own.
AI, Bring! and notifications are optional; configure them only when needed.

## Recover a forgotten password

A local Docker administrator can run the interactive recovery command:

```sh
docker compose -f compose.preview.yaml exec -it mealf python -m mealf.cli recover
```

For a source build:

```sh
docker compose exec -it mealf python -m mealf.cli recover
```

Enter the new password twice when prompted. Recovery changes the password and revokes
all device/browser sessions. Sign in again afterward. There is no public email-reset
endpoint. Do not delete the database, token file or volume to recover an existing account.

If setup reports that the household already exists, sign in with that account or use
local recovery. If a restart unexpectedly offers setup again, stop and verify that the
original `/data` volume is mounted before creating another household.

Source: [administration](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/ADMINISTRATION.md)
and [deployment](https://github.com/CLOUDCOOKCH/aircooker-server/blob/main/docs/DEPLOYMENT.md).
