# ADR 010: PWA-first delivery with the native client retained

Status: accepted by the user, 2026-10-21.

The user chose PWA-first after reviewing iPhone limitations and explained that no Mac is
available. Retain aircooker-ios and its tested code; pause its feature work. Implement the
primary client under aircooker-server/frontend and serve compiled assets at /app/ in the
existing container. Administration stays separate. Do not create a mandatory third repo.

Use React/TypeScript for maintainable stateful forms and planning views, Vite for a static
production build, IndexedDB transactions for records and outgoing mutations, and a service
worker for the application shell/cache. Node is a build dependency, not another running
service. Generate TypeScript API types from this repository's OpenAPI specification and
check generated drift in CI. Reuse backend business logic and the versioned sync protocol.

Browser authentication uses separate Secure, HttpOnly, SameSite=Strict access/refresh cookies
with explicit origin/CSRF validation. Never persist credentials/tokens in IndexedDB or web
storage. Keep the existing administrator cookies and native bearer-token API compatible.
Serialise refresh/sync across tabs; expired auth pauses work without deleting local edits.

Preserve the approved food/glass visual direction, five primary destinations, accessible
forms and review-before-apply. Adapt desktop composition rather than stretching a phone.
This is an operating product, not a landing page or static reproduction of the concept.

Accepted iPhone changes: incoming sharing uses paste/import (a Shortcut can be an optional
extension); WidgetKit widgets remain native-only; reminders use opt-in connected Web Push;
offline edits sync while the client runs/reopens, without promises of background execution.
Request persistent browser storage and expose failed writes/unsynchronised changes. No
claim of identical native glass rendering or full native feature parity.

The current native TestFlight acceptance is deferred. PWA release requires installability,
offline restart, two-device replay/conflict/deletion recovery, real browser testing,
accessibility/localisation, secure upgrades and single-container deployment. AI/Bring live
checks remain credential-gated. Preserve the original requirements except these explicit
delivery/platform changes; update the checklist with evidence rather than marking it done.
