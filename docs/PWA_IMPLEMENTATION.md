# PWA-first implementation and evidence

Explicit user decision, 2026-10-21: PWA-first; keep native code for later. ADR 010 and
PRODUCT.md replace native-only delivery/signing requirements. Other master product,
security, privacy and reliability requirements still apply. This is a functional development
client, not a declaration that the entire project or release checklist is finished.

## Implemented and tested

- Same-container `/app/` client and focused original administration console at `/`.
- Onboarding/setup, one-time administrator token, isolated Secure/HttpOnly rotating browser
  credentials, CSRF/origin checks and independent device sessions. No JS-stored auth secrets.
- Home, Calendar, Recipes, Pantry and Settings in the approved food/glass direction. Native
  code and original artwork retained independently; explicit demo never touches household APIs.
- Recipe editor/detail, searchable library, draft persistence, selected photos, fractions/
  decimals/ranges, proportional ingredient scaling, original source/provenance/notes/rating,
  optional nutrition editing. Nutrition is preserved as supplied, not inferred or rescaled.
- Civil-week planning, accessible assignment/move/duplicate/remove/cooked controls, drag
  alternative, bounded recurrence/exceptions, day/week copy, saved templates and leftovers.
- Basic pantry with period-bound shopping overrides and local ratings/history/variety/leftover
  recommendations with preview approval. Offline overrides retain their intended civil week.
- Durable import requests, polling, editable previews, explicit AI content consent, manual
  source/text fallback and cancellation delivery. No auto-save of extraction results.
- IndexedDB records/outbox/photos/draft removal commit atomically. Web Locks serialise sync
  across tabs; history/identity checks precede uploads/pushes; receipts are validated.
- Grouped suggestions replay the immutable full request after partial local acknowledgement;
  server slot collisions reject atomically and keep the local plan available for review.
- Rejected-photo isolation preserves unrelated outgoing work. Tombstones, rejected-copy
  recovery, retained server snapshots and explicit archived history rebuild preserve edits.
- Public-only service-worker shell, install manifest/icons, explicit updates, persisted-storage
  request and browser recovery export with photos. API/auth/media are never in its cache.
- English/German, light/dark, keyboard focus, named dialogs, reduced-motion and opaque fallbacks.
- Browser dependency attribution/version gate; Node remains build-only, not a runtime service.

Evidence: **151 backend tests**, **32 web core tests**, lint/types/format/OpenAPI/licence checks
and zero known npm advisories pass locally. Real Chromium smoke covers setup, offline recipe
save/reload, fractions, two-device commit ordering, deletion/rejected-copy recovery, meal
assignment, cooked leftovers, pantry, explicit import preview/save and cache separation.
The same script passes Axe WCAG2 A/AA and 2.1AA checks on its stated screens. Domain/unit
tests cover recurrence/copy/templates/suggestions; not every source control has browser E2E.

The independent visual/source reviewer inspected seven genuine desktop/phone/light/dark/DE
captures. One bounded pass fixed dialog names and singular serving copy; the reviewer scored
both resolved at that scope. The design plugin's launcher/specialist resources became
unavailable; the handoff used a fresh manual reviewer and no detector pass is claimed.

## Partial, unverified or planned

- [ ] Physical iPhone/Safari Home Screen install, storage eviction/lifecycle, standalone safe
      areas, real keyboard/VoiceOver/large-text/reduced-transparency and broader browser testing.
- [ ] Opt-in Web Push reminders and delivery/retry/permission management. No notification
      settings pretend this exists. Passkeys are also not implemented.
- [ ] Shared household recommendation preferences and acceptance learning.
- [ ] Guided non-recipe archive reconstruction and automatic browser-recovery JSON import;
      current archives/exports preserve data but these recovery paths remain manual.
- [ ] Template rename/slot editing, full recurrence browser acceptance and expanded suggestion
      collision UX/testing beyond tested atomic grouping/recovery.
- [ ] Source-photo import, broader HTML/caption/transcript extraction, language/quantity cases.
      Unsupported sources retain manual/AI fallback; no access-control bypasses are implemented.
- [ ] Live Bring!/AI compatibility and external response/error verification. Bring mutations
      remain capability-guarded; synthetic tests do not establish live compatibility.
- [ ] Original master backend work: safe cleanup/retention, admin deletion/destructive replacement,
      remaining typed API/quotas/security/load review, backups/release compatibility and docs.
- [ ] Stable image/release and reproducibility acceptance. PWA commit ff48270 passed all six
      AMD64/ARM64/security/browser/core CI jobs in run 39584288763 (see validation/github-pwa.json).
      Later pantry changes require their own exact-commit results.

iPhone incoming Web Share Target, native local notifications/biometric lock and WidgetKit
are deferred native capabilities, not promised pure-PWA functions. Foreground/reopen sync
and connected opt-in Web Push are the chosen browser constraints. Do not claim full native
feature parity or completed product acceptance.

See PWA.md for installation, development, behavior and recovery-format/security details.
