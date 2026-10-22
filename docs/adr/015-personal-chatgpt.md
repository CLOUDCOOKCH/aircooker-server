# ADR 015: Personal ChatGPT subscription connections

Status: accepted for the user-requested text-import milestone, 2026-10-22. Live provider
verification remains separate. This is an explicit optional extension requested after
the PWA-v1 scope freeze; it does not waive any production acceptance gate.

## Decision

Use OpenAI's documented OSS dynamic OAuth registration and public Responses endpoint.
Keep household login and existing API-key adapters unchanged. A standalone standard-library
Python helper completes the documented loopback flow on the user's own computer, then
hands the protected credentials to the self-hosted runtime over HTTPS. The PWA receives
only an expiring one-use pairing capability and redacted status, never OAuth tokens.

Use PyJWT 2.15.1 with the existing cryptography dependency for signature/claim verification,
rather than implementing JWT cryptography. The pinned MIT wheel includes its notice and
is covered by lock/attribution/dependency gates. Discovery and JWKS are restricted to the
documented OpenAI issuer/endpoints; redirects are refused. Identity/access signatures,
audience, nonce, subject/client binding and signed/granted scopes must agree.

Bind one connection to an authenticated mealf **session ID**. A device UUID can be supplied
when logging into the shared household and is insufficient as a personal-usage boundary.
Persist the owner and connection ID server-side with each approved import, use the exact
displayed model, and require explicit background consent for the durable worker. Check the
session/connection/model before disclosure and before accepting a late result. Keep import
receipts after source pruning so duplicate delivery cannot create another external job.

Store encrypted credential sets in SQLite under the existing local encryption key so
metadata and rotating tokens commit atomically. Serialize refreshes in the supported
single-process runtime and compare the prior encrypted value before committing. A
disconnect or concurrent reconnect cannot be undone by a late refresh. Preserve registration
mapping on explicit disconnect for same-account reconnect; new connection IDs invalidate
old consent. Exclude all new credentials and personal identity from portable exports.

The first adapter accepts supplied recipe text only. Use streamed Responses with
`store:false`, no tools or unsupported preview fields, bounded resource use and strict
provider-neutral schema validation. Only terminal `response.completed` with valid content
can produce an editable preview; explicit Save still creates the canonical recipe.
There is no automatic paid-provider fallback, cross-person pooling or account rotation.

## Alternatives and consequences

- A generic Continue-with-ChatGPT website callback is a different registration path; do
  not invent HTTPS NAS callbacks for the documented OSS loopback flow.
- Keeping tokens in the PWA would conflict with the privacy/session model and would not
  support durable backend jobs reliably.
- One household-wide subscription would let another member's activity spend the owner's
  plan and contradict current SIWC terms. Session ownership preserves the shared household
  while keeping this integration personal.
- A central callback/token broker would add mandatory hosted infrastructure and is rejected.
- Native Windows packaging/signing and a pure iPhone-only authorization flow are not part
  of this milestone. Python installation is a one-time desktop prerequisite, not a Mac or
  additional mandatory backend service.

See [setup, limits and evidence](../CHATGPT.md). Remaining platform/live/provider limitations
must be recorded rather than inferred from synthetic OAuth/model responses.
