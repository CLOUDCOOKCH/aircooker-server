# Recipe ideas

Open **Recipe ideas** on Home or in Recipes. Choose **Use what I have**, enter ingredients
(for example, spaghetti and minced beef), or choose **Surprise me**. The configured
household AI produces three complete proposals in the English/German interface language.
Check the full ingredient list: extra ingredients may be needed. This does not inspect
inventory or guarantee that everything is already at home.

Select **Review recipe** to edit quantities, servings and instructions in the normal editor.
**Save** explicitly adds that recipe to the local library and outgoing sync queue. Generating
or reviewing proposals never changes the library, calendar or Bring! list. Saved recipes can
subsequently be scheduled normally. Generated content retains provider/model provenance;
no nutrition, source attribution or photo is invented. The original peach is the placeholder.

## Configuration and privacy

Configure a text-capable household AI in Settings or `/admin/`. Existing Gemini, OpenAI,
OpenAI-compatible, Anthropic, Ollama, OpenWebUI and OpenRouter adapters are reused. Support
depends on the model/endpoint. This feature does not use a personal ChatGPT-plan connection
or silently fall back to another billing source.

The page displays provider, model and base URL and asks permission to send the request.
Ingredients mode sends your entered text and requested language/mode. Surprise sends an
empty ingredient string, even when earlier typed ingredients remain locally. Neither mode
uploads the recipe library, pantry, shopping list, calendar, credentials or a photo. The
server supplies a bounded generation prompt/schema. Cloud providers can charge per request
and apply their own retention policies.

Queued work is pinned to the displayed destination; configuration changes fail closed and
require renewed consent. New requests are limited to 20 per household hour and share the
configured AI quota with imports. Keys remain encrypted on the server; prompts, ingredient
text and provider responses are not application log fields.

## Reliability and offline use

### Troubleshooting Gemini and failed requests

Use an exact API model identifier, for example `gemini-3.8-flash`, rather than the display
name `Gemini 3.8 Flash`. With the Google Gemini adapter, the default base URL is
`https://generativelanguage.googleapis.com/v1beta`; do not append the model or
`:generateContent` to it. Model availability and permissions still depend on your provider
account. Gemini IDs containing whitespace are rejected before saving or contacting Google.
Other providers' identifiers are not rewritten. See Google's
[Gemini 3.8 model/API guide](https://ai.google.dev/gemini-api/docs/generate-content/whats-new-gemini-3.8).

Failed proposals show a localized recovery explanation and, for recognized failures only,
a fixed diagnostic code. `ai_model_or_endpoint_not_found` represents an upstream 404;
`ai_request_rejected` represents 400/422 and can indicate unsupported model options or
output schema. These classifications do not assert the exact provider-side cause.
Authentication, quota, timeout, blocked content, incomplete output and invalid recipes
remain separate. Unknown error text and provider response bodies are never echoed.
The Settings action opens Settings; expand **AI recipe import** to change configuration.
Generation still requires a deliberate new request after failure; reloading retains the
failed UUID instead of generating another billable batch.

The `/admin/` AI connection test sends a synthetic recipe, not household content. A known
provider failure is a failed configuration validation: provider-side 5xx failures return
HTTP 422 with an allowlisted error code rather than presenting this server as a broken
gateway. Upstream quota failures retain HTTP 429. Successful validated probes alone return
HTTP 200. No automatic retry occurs; credentials, response bodies and prompts are omitted
from the `ai_connection_test_failed` log event. DNS/connect/TLS failures have the separate
`ai_connection_failed` code; it does not distinguish those causes without container checks.
This preserves diagnostic JSON through proxies that replace 5xx error pages and does not
repair a disconnected tunnel or an unverified live provider configuration.

The administration's
`http_502`/`http_504` fallback means no readable API error code was received, so inspect
container and reverse-proxy logs; it is not proof of an invalid model, key or timeout.
A failed connection test does not isolate a Recipe ideas-specific failure. If the test
succeeds but generation fails, use the proposal's diagnostic code. Three recipes may take
longer than the small probe, especially with thinking models; adjust the supported timeout
only when a timeout is actually reported. Do not raise limits or silently resend to conceal
an unexplained failure. See Google's [troubleshooting guide](https://ai.google.dev/gemini-api/docs/troubleshooting).

The reported live deployment's immediate `http_502` returned Cloudflare HTML. Supplied
tunnel logs show historical refused origin connections, but not at that probe's time;
they do not establish its cause. A subsequent direct LAN health read succeeded. Local tests
use synthetic HTTP failures and an explicit 5xx-replacing proxy double; they do not
establish a live fix. Compare fresh tunnel and container logs at the exact test time.
A direct LAN read of `/api/v1/system/health` tests current reachability only, not AI access
or authenticated browser flows.

The user subsequently confirmed the saved API model ID and reported that the small
connection probe succeeds with structured output disabled. The same stored ideas job
still reports the old coarse `ai_provider_failed` code; its original upstream status
cannot be reconstructed from that code. Keep structured output disabled for this
investigation, reopen Recipe ideas, check the provider-consent box and explicitly choose
**Give me three ideas** / **Gib mir drei Ideen**. Reloading alone preserves the previous
request and does not call the provider again. New failures in `poc-20261022.10` retain the
more specific codes above. No live-generation success or exact schema defect is claimed.

Migration 015 persists requests/results in SQLite for the existing durable worker. The
client saves its UUID before sending: identical replay returns the original job, while a
changed body under the same UUID returns 409. Strict validation requires exactly three
bounded proposals with ingredients and steps. Creative generation has its own prompt,
separate from factual extraction. User text is untrusted data; it grants no tools or browsing.

Provider generation is not assumed idempotent. Recovery of a previously running job fails
the request rather than silently billing it twice. Interrupted/invalid/quota-limited/failed
requests show an error; the user can explicitly request another batch. Reconnection retries
delivery of the existing UUID rather than starting another generation.

The last form, request and downloaded results remain in this browser's household storage.
Offline users can read cached proposals, edit and save through the normal durable outbox.
New generation requires connectivity. Completed/failed server previews expire after 30 days:
text/results are removed while a minimal UUID/fingerprint receipt prevents replay. Cached
proposals remain locally until replaced or local household data is removed. Unsaved temporary
proposals are excluded from exports; saved recipes use ordinary export/sync behavior.

AI recipes can contain mistakes. Review ingredients, dietary restrictions, quantities and
instructions. They are not verified nutrition or food-safety advice. Local weekly meal-plan
recommendations remain independent of AI and use the saved library/history.

## Evidence

`tests/test_recipe_ideas.py` covers processing/replay, configuration pinning, crash recovery,
schema rejection, redaction, retention and all seven actual adapters over synthetic HTTP.
`scripts/recipe_ideas_browser_smoke.py` drives the real PWA/backend/SQLite/worker through the
Gemini adapter, replacing only provider HTTP: ingredient/random flows, explicit review/Save,
offline edit/reload/sync, cached results, malformed responses, EN desktop, DE phone down to
320px and Axe. This is not live-provider or physical-iPhone evidence. See the bounded
[UI review](validation/recipe-ideas-ui-review.md).

Published `poc-20261022.7`: all six exact-source CI jobs, both fresh native image gates,
public assets/scans/SBOM identities, anonymous pull and .6-to-.7 same-volume 5152 upgrade
pass. [Exact evidence](validation/github-recipe-ideas-preview.json) distinguishes generated
content over synthetic provider HTTP from published runtime and unverified live services.
