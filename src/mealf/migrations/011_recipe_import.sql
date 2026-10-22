CREATE TABLE import_source (
    id TEXT PRIMARY KEY,
    content_type TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    byte_count INTEGER NOT NULL CHECK(byte_count>0 AND byte_count<=8388608),
    data BLOB NOT NULL,
    created_at REAL NOT NULL
);
ALTER TABLE import_draft ADD COLUMN source_id TEXT REFERENCES import_source(id) ON DELETE SET NULL;
ALTER TABLE import_draft ADD COLUMN extraction TEXT;
CREATE TABLE import_ai_attempt (
    id TEXT PRIMARY KEY,
    import_id TEXT NOT NULL REFERENCES import_draft(id),
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    input_format TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('started','succeeded','failed')),
    error_code TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX import_source_age ON import_source(created_at);
CREATE INDEX import_attempt_age ON import_ai_attempt(created_at);
