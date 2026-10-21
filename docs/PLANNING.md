# Leftovers and meal suggestions

Leftover `portions` is a batch total. Active meal references reserve their serving counts,
including past cooked meals. Available portions equal total minus reservations; discarded
batches have zero available portions. A replacement meal releases its previous allocation
inside the same transaction before the new allocation is checked. Concurrent devices cannot
reserve the same last portions: one valid commit succeeds and the other fails with 409.

Editing a batch cannot reduce its total below bookings, switch its booked recipe or place
preparation after a booked meal. Deleting a batch with active bookings fails. Discarding
keeps booked meals intact but disallows new reservations; an existing reservation may be
moved, marked cooked or reduced. A scheduled leftover contributes no new recipe ingredients
to Bring projections. Preparation dates are preserved; no expiry/freshness is inferred.

Recommendations operate entirely on household data, without AI or external services:

- Expand the current week and the preceding 60 days of recurrence-aware calendar history.
- Prefer rated recipes, variety and recipes not recently marked cooked or repeatedly planned.
- Respect every occupied selected meal slot and current-week recipe usage.
- Use remaining prepared leftovers when their date and portions fit, without spending
  reserved portions again. Leftovers may intentionally reuse a planned recipe.
- Suggest recipes once by default; optional repeats support a small library.
- Return reasons and a read-only preview. Regeneration changes a deterministic tie-break seed.

There is no dietary classifier: choosing breakfast/lunch/dinner does not infer suitability
from ingredients. Richer household preferences and acceptance-specific learning remain work.
Previously accepted suggestions contribute to ordinary calendar history, rather than being
claimed as a separate trained model.

The API defaults to dinner, accepts explicit categories and optional portion overrides,
and returns a snapshot basis. `/suggestions/apply` commits a reviewed selection with a
request UUID. It rejects stale snapshots, occupied/duplicate slots, overwrites, recurrences
and cooked entries. An exact retry returns the persisted result even after restart; changed
content at the same request ID conflicts. Receipts are retained in SQLite and excluded
from non-secret exports.

The iOS engine uses the same versioned canonical fixture and explicitly selected local
approval. Local preview/selection/outbox are atomic and survive restart. Its normal sync
still sends individual ordered mutations: concurrent offline approvals can add multiple
dishes to a slot. This limitation is documented; the live API's transactional guarantee is
not falsely attributed to offline cross-device synchronisation.

When repeated suggestions are allowed, choose the least-used available recipe first.
Ratings, recency, frequency and deterministic seeded ordering rank recipes with equal use
counts. Leftovers retain their separate priority. A finite score penalty alone allowed an
extreme rating/history difference to repeat a recipe before the library was exhausted;
Python and Swift now enforce this ordering explicitly and test it over ten seeds.
