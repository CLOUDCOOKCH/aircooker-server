# ADR 003: Optional adapters and fail-closed external mutations

Status: accepted for development; live Bring verification pending.

Bring is unofficial and replaceable. Only UUID operations may modify owned entries.
Persist identity before calling the remote service and applied state afterwards. Never
adopt a manually created same-name item. Keep purchased history by shopping period and
suppress requirements already purchased during that period. If increases cannot safely be
distinguished, conservatively suppress them and surface the limitation.

The SDK documents UUID create/update/remove and pending/recent status; documentation is not
a runtime guarantee. A dedicated-list compatibility probe must succeed before automatic
mutations become available. Reports expire after 30 days and are scoped to SDK and list.
Production monitoring must disable mutations if identity or response schemas change.

AI is optional text transformation. Providers have distinct envelopes and capability flags.
No tools, host execution or AI-directed browsing exist. Deterministic structured extraction
is the default. Explicit per-import consent is required to use a configured AI provider,
including local providers, so the disclosure workflow is predictable.

Instagram, TikTok and YouTube adapters initially identify the source and attempt the same
public structured data path. No guaranteed video/transcript access is claimed. Source
specialisation and richer supplied-text extraction remain work for the import phase.
