# Pantry basics and food tastes

This is the locally tested food-setup extension for candidate `poc-20261023.3`, not a
published preview. The last published preview is `poc-20261023.2`.
See the [bounded review and evidence](validation/food-setup-review.md).

## Start with actual pantry stock

A newly configured household sees a nonblocking **Choose pantry basics** invitation on
Today. **Not now** dismisses it for the shared household. Upgraded households do not get
this pantry invitation again. At any time, open **Shopping → Pantry → Choose pantry basics**.
The picker searches 24 English/German staples grouped as Seasoning & oils, In the cupboard,
and Fridge & fresh. Nothing is preselected unless it already exists as available pantry
stock or you have a saved draft on this browser.

Select only what you actually have, then choose **Save my pantry**. Only selected missing
staples become pantry records; matching existing staples have their availability updated.
Deselecting an existing staple makes it unavailable rather than deleting it. Custom items
are untouched. **Not now** records completion without applying the selection. Draft
checkboxes survive reload; an applied selection clears that draft. Pantry records and
completion are committed in one local IndexedDB transaction and remain queued offline.

Available staples are excluded from shopping calculations until availability changes,
subject to the existing **Include this week** override. Exact curated EN/DE aliases match
translations such as Salt/Salz. Matching normalizes case, Unicode and whitespace; it does
not use fuzzy matching or infer that an ingredient with modifiers is equivalent. These
aliases affect pantry exclusion only: Bring! item identifiers and ownership rules remain
unchanged. Inspect the shopping requirements after editing pantry availability.

## Teach Recipe ideas your taste

First-use **Recipe ideas** opens twelve food cards unless an older queued idea request
already exists. Swipe right for **Like**, left for **Not for me**, or use the labelled
buttons. **Skip this food** removes that card's preference; **Back** lets you change the
previous decision. Choices and position persist locally after each decision. **Review my
choices** restarts the cards; **Save my taste** shares the current likes/dislikes and marks
setup complete. Save is available before the final card. **Not now** marks completion
without committing draft likes/dislikes. The draft remains available to resume later.
Open **Your taste** on Recipe ideas to edit again.

The twelve cards are rice, pasta, vegetables, chicken, beef, fish, beans & lentils, cheese,
mushrooms, spicy food, Mediterranean food and Asian-inspired food. These are shared
household tastes, not individual profiles, allergies or medically safe dietary restrictions.
Review every generated ingredient yourself. Selection and Save call no AI service and do
not generate recipes or change the calendar. Buttons provide keyboard alternatives to
pointer gestures; reduced motion suppresses the moving-card transform.

## Sharing, offline work and queued ideas

The shared profile contains likes, dislikes and the two setup-completion flags. Its
GET/PUT API is separate from entity sync. The browser persists an outgoing queue, a
server snapshot and separate pantry/taste drafts in household/device-bound storage.
Pending profile changes contribute to sync status. Entity/history validation runs first;
a preference failure cannot prevent the preceding recipe sync. Preserve browser data
while work is pending; private pending-work exports include the profile queue and drafts.

On the server, the last committed save wins for each changed field, irrespective of device
clock. A stale base revision is accepted with a conflict indicator. Omitted fields retain
current values; likes/dislikes lists replace their respective fields. Concurrent changes
that leave one food in both lists are rejected and retained for recovery. A stable request
UUID/body replays once; another device or changed body cannot reuse its receipt. A slow
older profile response cannot overwrite a newer accepted browser snapshot.
Before sending queued profile writes, sync checks the server revision. A backwards revision
returns `sync_history_changed` without a PUT or false synced status. Use the existing
explicit server-history recovery: it archives the raw food state alongside entities/outbox
in the same IndexedDB transaction, then clears the active profile snapshot/queue. Unfinished
setup drafts remain. Only after recovery can the lower restored profile load; archived
choices remain in the private pending-work export and are not replayed automatically.

An explicitly requested new idea batch freezes the effective saved preferences in its
request alongside the consented provider/base URL/model. Editing taste later does not
rewrite or resend an already queued batch. Older jobs without preferences retain their
original request identity. The provider receives the selected food names, requested
language/mode and entered ingredients; it does not receive the whole pantry or recipe
library. Recipe ideas keeps its explicit provider-consent checkbox and review/Save flow.
See [Recipe ideas](RECIPE_IDEAS.md) and the [API contract](API.md#household-food-profile).

## Import preview and operations

Household imports now show a short transfer notice and **Prepare AI preview**, replacing
the repeated household-AI checkbox, default-provider paragraph and transfer-consent
checkbox. Deliberately preparing the preview authorizes that disclosed transfer when
household AI is configured; the API still requires explicit consent fields and pins the
known public destination. Offline imports can bind a previously cached public AI
configuration; no unknown destination is guessed. Configuration changes fail closed for
queued work. Personal ChatGPT selection/background consent remains a separate flow.
Preparing or reviewing an import never saves a recipe automatically.

Migration 016 creates the shared profile and device-bound replay receipts. Existing
households start with pantry setup complete and empty tastes; fresh households can see
the invitation. Export format v4 adds the non-secret profile, not receipts or credentials;
the ZIP envelope remains version 1 and formats 1–3 remain importable. See
[backup compatibility](BACKUP.md), [privacy boundaries](security/PRIVACY.md) and
[ADR 017](adr/017-food-onboarding.md).

Retain the existing Docker volume, custom port/command/healthcheck and browser storage
when upgrading. Save open edits before accepting the PWA update. No database reset,
reinstall or re-pairing is required by this extension. Candidate image publication,
both-architecture runtime/security gates and current-source Chromium/WebKit CI remain
pending in this documentation handoff. Live AI/Bring!, physical iPhone and production-v1
acceptance remain unverified.
