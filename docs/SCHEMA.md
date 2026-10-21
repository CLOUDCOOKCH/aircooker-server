# Database schema and invariants

Schema is executable in `src/aircooker/migrations`. Migrations run once in a locked startup
transaction, tracked by filename. Released migrations must never be edited in place.

| Table | Responsibility and invariants |
| --- | --- |
| household | Exactly one row (`id=1`); account, settings, Argon2id hash and stable server identity |
| device / session | Independent sessions; hashed opaque access/refresh tokens, expiry and revocation |
| refresh_history | Rotated-token replay detection revokes the corresponding session |
| entity | Atomic canonical snapshots keyed by kind/UUID, revision and tombstone |
| change_log | Server-committed delta sequence plus immutable random commit token; sequence alone is not proof of ancestry after restore |
| mutation | Device-scoped replay result and immutable request fingerprint |
| recipe_media | Immutable UUID/JPEG BLOBs, source/canonical checksums, 1 MiB per image and 256 MiB household quota |
| recipe / recipe_ingredient / recipe_step | Normalised domain projections with ingredient ordering and recipe foreign keys |
| meal_plan_entry / leftover / pantry_item | Indexed date/category projection and explicit recipe/leftover links |
| suggestion_application | Device-scoped request fingerprint/result receipts for atomic live preview approval and replay |
| background_job | Deduplicated jobs, leases, fencing token, generation, retries, redacted error code |
| import_draft | Pending/preview/needs-input/confirmed/cancelled state, warnings and provenance |
| bring_owned_item | Period/requirement/list ownership ledger, external UUID, applied state and purchase history |
| rate_limit / audit_event | Durable request buckets and local security-operation audit events |

Templates and recurrence rules are represented in typed entity snapshots. Recommendation
preferences are currently device-local; shared household preferences remain incomplete.
Dedicated projections, separate rating history, acceptance-specific learning,
shopping-period records and per-device sync cursors are still incomplete. The schema is an
incremental implementation, not a claim that all evaluated entities have been delivered.

Numbers are decimal text. UUIDs have no business meaning. Meal dates are ISO date-only
strings; timestamps are UTC. A recipe soft deletion preserves foreign key targets. Queue
payloads can include household source content and must stay inside protected `/data`.

Retention is intentionally conservative: tombstones, mutation replay records, Bring purchase
history, suggestion-approval receipts and completed jobs are retained. Rate-limit buckets expire when a subsequent request
arrives. Session/job/content retention policies and compaction with full-resync recovery must
be implemented before stable release. No unsafe automatic cleanup is enabled.
