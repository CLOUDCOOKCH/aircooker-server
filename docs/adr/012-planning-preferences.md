# ADR 012: shared planning defaults and explicit-approval learning

Status: accepted implementation direction, development release gates still apply.
Date: 2026-10-21.

Keep recommendations local-first and independent of AI. Store a small household preference
snapshot and bounded accepted-recipe counts in SQLite. Typed authenticated endpoints expose
these separately from the five sync entity kinds, preserving retained native v1 decoders.
PWA caches support offline scoring; settings edits remain durable drafts until explicit
online save. Whole snapshots use server-ordered revisions and device-bound idempotent
receipts, never client-clock conflict authority.

Record learning only inside successful explicit plan approval transactions and once per
recipe per approval. Receipt replay never teaches twice. Cap the score bonus and keep use
count as the strict variety priority. Do not infer cooking from acceptance or create cloud
recommendation dependencies. Explain previously accepted suggestions in ordinary language.

Portable household export advances to v3 to include non-secret preferences/learning; retain
v1/v2 import. Keep the ZIP envelope at v1 with a versioned household manifest. Validate
references and restore all state in one transaction. Exclude session/credential/replay state.
See PLANNING_PREFERENCES.md for limits, differing retained engine portion defaults and evidence.
