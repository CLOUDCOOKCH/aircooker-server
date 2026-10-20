# ADR 002: SQLite and server-ordered whole-entity sync

Status: accepted for development.

SQLite fits one household and a single-container deployment without Redis or PostgreSQL.
WAL permits readers alongside one writer; databases must reside on a local filesystem.
Never put the live database on SMB/NFS. Use SQLite's online backup API, not a raw copy of a
live database file without its WAL state.

Each domain write, change sequence, idempotency result, relational projection and shopping
job enqueue commits in one transaction. Last valid server commit wins. Device timestamps
are diagnostic only. Base revisions expose conflicts but do not prevent an explicitly
valid stale write. Whole-entity replacement prevents inconsistent partial JSON merges.
This intentionally does not merge concurrent disjoint ingredient edits; document that
tradeoff rather than quietly inventing field-level semantics.

Tombstones are permanent in the development protocol. A stale upsert returns
`rejected_tombstone`; the client preserves the unsent draft and surfaces an error. A future
release needs a recovery/export UI and a generation-aware full-resync protocol before
compacting the change log. Backend identity is pinned locally to prevent mixing households.
