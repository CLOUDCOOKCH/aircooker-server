# ADR 016: Explicit creative recipe ideas

Status: accepted, 2026-10-22. The user requested ingredient-based and random AI recipes as
an explicit addition to the previously frozen PWA v1 scope.

Factual imports must not invent missing content. Creative suggestions therefore use a
separate prompt, strict schema, endpoints and temporary table while reusing configured
household providers, quotas, encrypted settings and the worker. Exactly three complete
proposals retain generated provenance. Only the normal editor's transactional Save/outbox
creates a library recipe. Local weekly recommendations remain AI-independent.

Displayed destination and explicit transfer consent belong to the immutable request.
Surprise excludes typed ingredients. Neither mode sends household inventory/library.
Configuration changes fail closed. IndexedDB preserves input/request/results; SQLite
persists job state. Delivery replay is idempotent, but generation is not assumed so:
recovery of running work fails rather than automatically making another chargeable call.
Completed previews expire after 30 days, retaining only minimal replay fingerprints.

No new infrastructure, packages, native UI, personal ChatGPT pooling, image generation,
nutrition inference or automatic calendar/Bring! mutations. API-major/sync-protocol stay 1.
