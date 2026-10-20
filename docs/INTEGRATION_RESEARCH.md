# Integration research — 2026-10-20

## Bring shopping lists

Inspected [miaucl/bring-api](https://github.com/miaucl/bring-api) at immutable revision
[`b43bc2fcd27b71732ced76ade3294fcdaab0a673`](https://github.com/miaucl/bring-api/tree/b43bc2fcd27b71732ced76ade3294fcdaab0a673).
The repository identifies the service as unofficial and uses the MIT license. PyPI lists
version 1.1.2; the packaged wheel is pinned independently of the reference checkout.

`bring_api/bring.py` implements `get_list` at `/v2/bringlists/{list}` and UUID-bearing batch
updates at `/v2/bringlists/{list}/items`. `types.py` models `purchase` and `recently` groups,
with item UUID, item name and specification. Do not use the name-only convenience API.
Readback, duplicate UUID handling, complete/remove semantics and partial failures require
live verification. No real account was contacted during development.

A runnable probe exists in `scripts/bring_compatibility.py`. It only removes the UUID it
created, compares unrelated baseline items before/after and requires explicit dedicated-list
configuration. A compatibility report is evidence for one list and SDK version, not official
support or contractual permission. Bring terms and current integration restrictions still
need operator/legal review before public distribution.

## AI

Reviewed [OpenAI chat API](https://platform.openai.com/docs/api-reference/chat/create) and
[Ollama chat API](https://docs.ollama.com/api/chat). Adapters deliberately separate OpenAI
choices/messages, Anthropic content blocks and Ollama message/done envelopes. Anthropic and
OpenWebUI documentation retrieval did not succeed in the research tool; those adapters use
known wire formats, tested with synthetic responses, and need current documentation and live
compatibility verification before release. No provider's image or structured-schema support
is assumed. All adapters are text-only; JSON response mode is administrator opt-in.

## Apple

[Apple's Xcode requirements](https://developer.apple.com/xcode/system-requirements) currently
list Xcode 27 and iOS 27; the native project targets iOS 26+ to cover current and preceding
major releases. Core validation used Swift 6.2.1 on Linux, which is not an Xcode or SDK test.
A compatible macOS runner with production Xcode 27 must validate native targets.

[App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) were located
but no App Review compliance assessment is complete. TestFlight/App Store preparation needs
an accessible functional demo, privacy details, current SDK/signing verification and genuine
screenshots. No review acceptance or distribution capability is claimed.

## Recipe sources

JSON-LD extraction can only see public returned content. Platform identification does not
establish video/caption/transcript access. No password collection, DRM circumvention,
authenticated scraping or anti-bot bypass is implemented. Copyright and access permissions
remain the household's responsibility. Preserve attribution and original URL.
