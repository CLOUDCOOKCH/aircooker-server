# Personal ChatGPT recipe imports

mealf can connect an eligible personal ChatGPT account through OpenAI's supported
open-source Sign in with ChatGPT flow. This first version accepts **recipe text only**.
It is optional, separate from household API-key providers and the household login.
No Mac, ChatGPT password, API key, copied browser cookie or central mealf service is needed.
An eligible plan, available allowance and working outbound HTTPS are still required.

## Connect from Windows

1. Update to `ghcr.io/cloudcookch/mealf-server:poc-20261022.2`, preserving
   its `/data` volume and existing port/command/healthcheck configuration, including
   `5152:5152`. Open the PWA using its valid **HTTPS** address and sign in to your household.
2. Open **Settings → Your ChatGPT plan**. Confirm that this is your personal account and
   browser session. Select **Connect ChatGPT** to generate a one-use code valid for ten
   minutes. Do not share or screenshot a real code.
3. Download the connector using the link in that section. Install Python 3.10 or newer on
   your Windows computer if needed. Open Terminal/PowerShell in the download folder and run
   the displayed command, replacing the example origin with your own:

   ```powershell
   py -3 mealf-connect-chatgpt.py --server https://mealf.example.com
   ```

   If your installation provides `python` instead of the Windows `py` launcher, use
   `python mealf-connect-chatgpt.py --server https://mealf.example.com`.
   Do this on the **computer running your browser**, not in the NAS/container terminal.
4. Paste the code when prompted. Input is hidden and the code is not a command-line
   argument. The connector opens OpenAI's own sign-in/consent page. Check the account and
   authorize plan usage if you want it; identity sign-in alone does not enable extraction.
5. Return to mealf. Select **Choose an available model**, choose a model returned for your
   account, and Save. Availability is not guessed from hardcoded model names.

The helper is a downloadable, inspectable Python file using only the standard library.
It binds an ephemeral port on `127.0.0.1`, validates the one-use callback state and PKCE,
exchanges the code locally, and transfers credentials to your server over verified HTTPS.
Your server verifies ID/access-token signatures, issuer, audiences, nonce, account/client
binding and granted permissions. The helper writes only a non-secret local host identifier;
it does not save OAuth tokens on the computer. The server retains its own distinct host ID.
This uses OpenAI's documented self-hosted-runtime handoff, not an arbitrary NAS callback
or consumer `backend-api` endpoint. Normal proxy/certificate trust remains enabled.

`--language de` provides German terminal instructions. Linux/macOS can run the same file
with `python3`; actual platform test evidence is listed below rather than inferred.

## Import a recipe

Open **Recipes → Import recipe → Link or text**. Choose **My personal ChatGPT plan** in
**AI account for this import**, paste recipe text, and review the displayed account/model.
Confirm the disclosure, which also explicitly permits your server to finish this particular
import after the app closes. Select **Prepare preview**, edit/check the result, then Save.
Preparing or viewing a preview never creates a recipe automatically.

This first version does not send photographs, attachments, PDFs, video or fetched website
content through the personal connection. Existing household-provider media imports and
local English/German photo OCR are unchanged. Text/images/files supported by OpenAI's
underlying protocol do not imply that this first mealf path implements all those inputs.

A prepared local import keeps the exact connection/model and consent in IndexedDB. Wait
until the queued import appears before closing/reloading. It can survive an offline reload
and deliver after reconnecting. OAuth credentials stay on the server, never in browser
storage or recovery exports. A changed session/connection/model requires source review and
a new approval; an old queued import is never rebound to another account automatically.

## Personal ownership and disconnection

The connection belongs to the **authenticated mealf session**, not a supplied device UUID
or the shared household account. Another browser session, even one claiming the same device
UUID, cannot view/use it. Other household members must connect their own account. Do not
let someone else operate a browser session connected to your personal plan. Reviewed recipes
become ordinary shared household recipes; sharing the result does not share the connection.

Access-token refresh is serialized and rotating credentials are replaced atomically. A
reconnection gets a new connection identity, invalidating previously approved jobs. Ordinary
mealf cookie refresh retains the session; signing out, revoking it or letting it expire stops
pending personal jobs. Signing into a new mealf session requires a fresh connection. This
first version supports one ChatGPT registration per mealf session, with same-account
reconnection; it does not offer a multiple-account picker.

**Disconnect ChatGPT** immediately stops local use and attempts remote session revocation.
If revocation cannot be confirmed, mealf says so; also disconnect the app in ChatGPT Settings.
Signing out of mealf alone is not a confirmed remote OAuth revocation. Expired pairing data
and credentials attached to revoked/expired mealf sessions are cleared by bounded hourly
maintenance. The minimal import ownership receipt remains with replay history. Password
recovery/session invalidation cannot cause a worker to reuse an old personal connection.

Keys/tokens are encrypted on the self-hosted server, excluded from portable household
JSON/ZIP exports and absent from job payloads/status. Sensitive SQLite disaster-recovery
snapshots can contain encrypted tokens and must remain protected with their encryption key;
see [backup policy](BACKUP.md). No token or personal account is bundled in the image.

## Failure recovery and privacy

- **Code expired/already used:** Cancel and prepare a new connection in Settings.
- **Declined consent/ineligible plan/workspace:** extraction stays disabled. Authorizing
  identity alone does not grant plan usage; check OpenAI access and reconnect if desired.
- **No available models:** check the account/workspace or use a household API-key provider.
- **Wrong account during reconnect:** the verified identity must match the saved registration;
  it is not silently replaced. A different account needs a separate mealf session in this
  first version. If the registration was removed in ChatGPT, a new session may be needed.
- **Interrupted, rejected or malformed result:** the source stays reviewable; no partial
  streamed answer is treated as a successful recipe. Review and explicitly retry.
- **Allowance exhausted or unavailable:** check ChatGPT usage, wait if appropriate, then
  review and retry. No automatic account rotation or switch to paid API billing occurs.
- **Network/certificate failure:** verify HTTPS, system clocks, outbound access to
  `auth.openai.com` and `api.openai.com`, and trusted certificate/proxy configuration.
  Never disable certificate verification. Reconnect if a rotating token can no longer be used.

Recipe text and its extraction instructions are sent to OpenAI only for your explicitly
approved import. Requests use Responses with `store:false`, `stream:true`, no tools, bounded
content/output/time, strict schema validation and terminal completion checks. OpenAI's own
account/data-use terms still apply. Using your plan here consumes its allowance; it does not
create extra usage or expose your existing ChatGPT conversations.

## Evidence and current limits

Automated evidence covers real JWT signature/identity checks, real loopback callback/PKCE,
one-use/expired/cancelled capabilities, session isolation, token refresh/revocation, encrypted
storage, restart, late cancellation, streamed errors and reviewed saving. Browser acceptance
uses the real PWA/server/queue/helper callback, English desktop/German dark phone/Axe, and
offline queued import replay. OpenAI HTTP responses and the helper HTTPS-origin routing in
that fixture are explicitly synthetic; no disabled TLS verification is used.

The standalone file passes without server packages on Windows Server 2025 with Python
3.10.11 and 3.12.10. All six source CI jobs and both fresh native image gates pass; the public
image and .1-to-.2 same-volume 5152 upgrade are verified. See [exact evidence](validation/github-chatgpt-preview.json).
Windows callback/PKCE fixtures do not verify a real OpenAI browser sign-in. Live
OpenAI registration, allowance eligibility and extraction require the user's real sign-in
and are **unverified until recorded separately**. This feature is not production-v1 approval.

Official references checked 2026-10-22:
[OSS overview](https://developers.openai.com/siwc/token-sharing-open-source),
[registration](https://developers.openai.com/siwc/token-sharing-open-source/sign-in),
[self-hosted handoff](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms),
[inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference),
[preview limits](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations),
[sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions),
and [terms](https://openai.com/policies/sign-in-with-chatgpt-terms/).
