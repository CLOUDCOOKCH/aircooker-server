# ADR 007: Commit proofs and snapshots for restore recovery

Status: accepted for development, 2026-10-21.

A SQLite backup can roll the server's sequence backwards. Later writes can reuse the same
sequence values on a different branch, so comparing integer cursors alone is insufficient.
A device can also acknowledge a write and stop before pulling its corresponding delta.

Assign every committed change a random 128-bit token in the same transaction as the domain
write and replay receipt. Migration 005 assigns tokens once to existing retained changes.
Expose the current head and the proof at a requested revision through authenticated state
reads. Return cursor tokens on deltas and revision tokens on new mutation receipts. Native
clients retain the latest observed proof even when their delta cursor has not advanced.
A proof identifies retained history; it is not a password, signature or authorization token.

Clients preflight before uploads, then include a checkpoint on pushes and the cursor token
on pulls. The server validates those anchors within the relevant SQLite transaction. A later
append preserves an earlier proof; a restored divergent branch does not. This also protects
the interval between preflight and an actual mutation request. Existing API-major/sync 1
clients may omit these optional request fields but do not receive this protection. The
updated native client requires the extended contract, pinned separately in its repository.

Full recovery is explicitly initiated in the native app. Snapshot pages query the latest
change for each identity at or before a fixed anchor, including tombstones. They order by
kind/UUID, cap the page at 100 records and target 2 MiB of payload (one indivisible record
may exceed that target). Later edits do not change previously anchored content. Each page
revalidates the anchor. This avoids a server-side snapshot queue, long-lived transaction or
unbounded whole-household response. Retained history is necessary; compaction is not enabled.

The native client stages those pages durably. Only a final local transaction archives all
active cached records and every outstanding envelope, replaces the local projection with
the verified snapshot, replaces its cursor/proof, and clears the old outgoing queue. Cached
photos and earlier archives remain. Recovery never automatically replays pre-restore changes
or silently changes household identity. Interrupted staging resumes without uploading those
changes. Reference-safe restoration beyond recipe copies remains separate work.

This deliberately costs additional local storage and occasionally requires administrator/user
attention after restore or an older-client upgrade. Silently resetting a cursor could lose
local work, preserve ghost records, reintroduce deleted content, or overwrite restored data.
A per-process generation would instead force unnecessary recovery after every normal restart.
