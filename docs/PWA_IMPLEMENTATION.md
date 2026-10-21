# PWA-first implementation and evidence

User-confirmed direction, 2026-10-21: make the PWA primary and retain the native iOS code for
later. ADR 010 and PRODUCT.md supersede the original native-only distribution requirements.
All other recipe/planning/security/privacy requirements remain in force. No third mandatory
repository or running infrastructure service is introduced.

## Delivered foundation

- Secure, HttpOnly, rotating browser session cookies, distinct from console cookies and
  compatible with native bearer sessions. Explicit origin/CSRF checks and token-free JSON.
- PWA bootstrap protected by the same local one-time token and transactionally locked setup.
- Credential expiry/logout/replay and Unicode username checks: six backend tests pass.
- Optional sync-history headers make reviewed import confirmation transactional with its
  history check; a backend test proves a mismatched/incomplete proof creates no recipe.
- React/TypeScript/Vite dependencies are pinned with an npm integrity lock. TypeScript 5.9.3
  satisfies the API generator's declared peer range; no forced peer dependency bypass.
- TypeScript API types are generated from canonical OpenAPI, with CI drift checks.
- IndexedDB records, outbox, photos and editor-draft removal share a transaction. Complete
  snapshots validate before commit; leftovers cannot be overbooked by competing tabs.
- Foreground sync validates server identity/history before uploads, checks receipts, keeps
  rejected drafts/queues and isolates permanent import errors. Demo sync is guarded off.
- Nineteen Node tests using fake IndexedDB pass. Strict types/format checks pass. npm reports
  no known advisories in the current full lock, not a guarantee of absence of vulnerabilities.

These are foundation tests, not evidence of an installed/running PWA. The full expanded backend suite passes: 143 tests. Ruff lint/format, mypy, OpenAPI drift,
frontend strict types/format, all 19 offline/API tests and the full npm advisory audit pass
locally. Remote CI and real-browser integration remain separate gates.

## Work still required

- [ ] Visible glass/food interface: Home, Calendar, Recipes, Pantry, Settings and onboarding.
- [ ] Real cookie-auth browser connection and two-device, restart/offline sync scenarios.
- [ ] Recipe editor/detail, scaling, image preparation/cache, original attribution/nutrition.
- [ ] Date-only recurring calendar, move/copy/duplication, weekly templates and leftovers.
- [ ] Pantry exclusions, local weekly suggestions, review-before-apply and shared preferences.
- [ ] Durable import UI, editable preview, explicit AI consent and reliable cancellation.
- [ ] Server-history rebuild and rejected-mutation recovery/export with preserved local data.
- [ ] Manifest/icons, service worker, safe updates, install guidance and storage failure UX.
- [ ] Opt-in Web Push reminders, with browser-platform limitations documented.
- [ ] One-container static build/serving, Docker/browser tests and multi-architecture CI.
- [ ] EN/DE, keyboard/screen-reader/large-text/light-dark and actual iPhone verification.
- [ ] Dependency attribution/security review, release docs and remaining master checklist.

No incoming iPhone Share Target or pure-PWA WidgetKit capability is claimed. Use URL/text
paste/import; an optional Shortcut may be documented. Face ID via passkeys would require
separate implementation and differs from the deferred native local biometric lock.

## Development checks

Node 24+ and the backend's Python environment, without a Mac:

```sh
cd frontend
npm ci --ignore-scripts
npm run api:generate
npm run typecheck
npm run format:check
npm test
npm audit --audit-level=high
```

The UI build/installation flow is not ready at this foundation stage. Do not present an
illustrative design image as a running PWA capture or mark the app release-ready.
