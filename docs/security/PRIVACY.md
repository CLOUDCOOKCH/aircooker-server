# Food setup and import privacy boundaries

Scope: the pantry/taste extension, 2026-10-23. This supplements the existing
[security model](../SECURITY_MODEL.md), [AI guide](../RECIPE_IDEAS.md) and
[backup guide](../BACKUP.md); it is not a new whole-product privacy assurance.

Pantry availability and saved likes/dislikes belong to the shared household account and
are visible to its authenticated devices. Completion flags also belong to the household.
Draft card position/selections and unsent changes persist in this browser's household/
device-bound IndexedDB storage. The host/browser operator can access that data; it is not
an encrypted personal vault. A private pending-work export includes drafts and queued
profile changes, so protect it like other household data.

Selecting foods or saving the profile contacts no AI service. An explicit, consented Recipe
ideas request includes a frozen snapshot of liked/disliked food names, requested language/
mode and any ingredient text. The provider receives neither the complete pantry nor the
recipe library, calendar, shopping list or credentials as request content. Preferences may
reveal household tastes; they do not constitute allergy or medical restrictions. Cloud
provider charges and retention policies apply. Existing temporary idea retention is
unchanged: server terminal content expires after 30 days, while downloaded proposals can
remain locally until replaced or household data is removed.

Household imports display a short transfer notice and an explicit **Prepare AI preview**
action. That deliberate action supplies consent when configured AI is used; it does not
authorize saving the recipe. Offline queueing uses a known cached public provider/base URL/
model only. A changed destination requires renewed review rather than silent rebinding.
Personal ChatGPT connections and their explicit background consent remain session-scoped
and separate. See [personal connection privacy](../CHATGPT.md).

Portable household export v4 includes the non-secret profile. It excludes preference replay
receipts, integration keys/tokens, session secrets and queued provider job internals. A
sensitive SQLite backup has different contents and needs operator protection. Private
pending-work recovery exports are separate from portable server household exports.
Profile endpoint access uses existing authenticated-session and browser CSRF protections;
PUT is device-rate-limited and replay receipts bind a request to the authenticated device.
No new analytics, tracking or hosted account is introduced. Test captures use a disposable
synthetic household; no live AI/Bring! or physical-device privacy acceptance is claimed.
