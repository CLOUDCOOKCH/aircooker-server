# ADR 005: Immutable bounded recipe photos and portable archives

Status: accepted for development, 2026-10-20.

Store normalised JPEG photos as SQLite BLOBs. Each asset is at most 1 MiB and the household
media quota is 256 MiB. At this scale SQLite offers an explicit atomic boundary for restoring
media, recipes, historical references, tombstones and sync changes. It also includes media
in the online disaster backup. `/data/media` remains reserved for a future measured migration
to larger filesystem assets; it is not currently the recipe photo store.

The authenticated multipart PUT uses a client-generated UUID. It is immutable: retries of
identical source or canonical bytes return the original metadata; different content at that
ID fails with 409. The server validates JPEG/PNG/WebP, bounds input bytes/pixels and re-encodes
a fresh JPEG after orientation correction, dropping source metadata. Recipes may reference
only existing media. Native SQLite persists prepared photo bytes, recipe and outgoing
mutation together, then sync uploads the photo before pushing its recipe. Photos remain
available offline after restart. Photos are not sent to an AI provider by this API.

For small households, JSON export v2 embeds base64 media. Larger libraries use a protected
ZIP tempfile and streaming HTTP transfer. The manifest is versioned, members have exact
allowlisted UUID names and checksums, and restore never extracts member paths. Validate
media before one transactional merge; reject duplicate entity IDs rather than overwrite.
Version-one JSON imports remain supported. Sensitive backups remain a separate local
administrator operation.

Consequences: SQLite/WAL and backups grow with photos; quotas need visible management.
The development implementation retains unreferenced media and crash-orphaned transfer
files rather than risk deleting offline references or an active export. Safe garbage
collection, export cleanup, quota-management UX and destructive replacement with explicit
confirmation remain release work. ZIP parsing still requires broader resource/security
validation. Apple ImageIO/PhotosPicker sources require an Apple SDK/device test.
