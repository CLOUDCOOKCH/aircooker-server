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
| import_source / import_ai_attempt | Bounded private immutable attachments and redacted provider-attempt history; source UUIDs never grant public access |
| bring_owned_item | Period/requirement/list ownership ledger, external UUID, applied state and purchase history |
| push_subscription | Per-device/session notification credentials encrypted with the vault; endpoint hash unique, bounded preferences and safe health fields |
| push_delivery | Accepted receipt unique by subscription/civil date/category; subscription deletion cascades |
| planning_preferences / planning_preference_receipt | Whole household defaults, monotonic server revision and device-bound replay receipts |
| suggestion_acceptance | Bounded count of distinct recipe choices in successfully approved plans, never inferred cooking history |
| rate_limit / audit_event | Durable request buckets and local security-operation audit events |

Templates and recurrence rules are represented in typed entity snapshots. Shared recommendation defaults and accepted-recipe counts use explicit tables with cached
PWA snapshots; native preference interfaces remain device-local.
Dedicated projections, separate rating history,
shopping-period records and per-device sync cursors are still incomplete. The schema is an
incremental implementation, not a claim that all evaluated entities have been delivered.

Numbers are decimal text. UUIDs have no business meaning. Meal dates are ISO date-only
strings; timestamps are UTC. A recipe soft deletion preserves foreign key targets. Queue
payloads can include household source content and must stay inside protected `/data`.

Pantry shopping overrides carry `include_week_start`, a Monday-only civil date. An available
staple is included only in that period; another week's projection automatically excludes it.
Clients should send the intended week, including while offline. Legacy undated writes are
bound to the household's current week on first acceptance; retries retain their original
receipt and cannot extend it. Undated archive restores disable the temporary override.

Migration 006 adds the projection column and publishes new canonical pantry revisions for
active legacy overrides, deriving their period from the previous server acceptance timestamp
in the household time zone. It never rewrites old change-log rows, commit proofs or mutation
receipts. Schema, backfill, new commits and migration marker commit together or roll back.

Retention remains conservative. Hourly bounded passes prune eligible terminal import/source
payloads, old diagnostic rows and unreferenced long-expired sessions, preserving replay
identities and all pending work. Startup-only cleanup removes stale known transfer ZIPs.
Canonical tombstones, sync proofs/mutation receipts, Bring ownership/purchases and media
remain retained for offline safety. Full compaction/quotas are release work. See RETENTION.md.


Migration 007 adds device-scoped Web Push state. It does not rewrite sync entities or old
commits. The VAPID private key is encrypted separately in the config vault; neither
subscriptions nor delivery secrets enter household exports. Job payloads refer to subscription
UUID/date/category, never the endpoint/key. See REMINDERS.md for delivery invariants.

Migration 008 adds shared planning preferences/replay receipts and accepted-suggestion counts.
It does not add unknown sync entity kinds, rewrite old commits or fabricate legacy learning.
Approval increments, meal writes and replay receipts commit together. Household export v3
includes non-secret preferences/counts; see PLANNING_PREFERENCES.md.

Migration 009 adds import request fingerprints and terminal timestamps with indexed retention
queries. Known source receipts backfill in bounded batches; unknown records stay exempt,
legacy terminal records receive a fresh grace period, and schema/data/marker commit together.
Internal retention fields do not become client import response fields.

Migration 010 adds bounded `recognized_text` to import previews. Existing rows remain
NULL; uploaded image UUIDs use the existing immutable media store and job payload. No
entity revisions, sync identities, old change logs or request fingerprints are rewritten.
Terminal OCR text follows preview retention; pending work and media remain retained.

Migration 011 adds private AI import sources, nullable source references and validated
extraction previews, plus a separate attempt ledger. Released migration 010 is unchanged.
The migration preserves queued photo imports, recognized text, household identity and
existing replay fingerprints. The new image/source/destination receipt fields are included
only when supplied; older request receipts remain byte-for-byte compatible. Recipe
metadata is additive, with legacy mutation defaults omitted from replay fingerprints.
Transient AI sources expire after seven days unless queued work still references them;
attempt history expires after 90 days. Existing photo media retention is unchanged.
