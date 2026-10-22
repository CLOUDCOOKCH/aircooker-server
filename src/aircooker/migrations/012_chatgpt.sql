CREATE TABLE chatgpt_host (slot INTEGER PRIMARY KEY CHECK(slot=1), host_id TEXT NOT NULL);
CREATE TABLE chatgpt_connection (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE REFERENCES session(id) ON DELETE CASCADE,
    client_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    label TEXT NOT NULL,
    credentials TEXT,
    expires_at REAL NOT NULL,
    earliest_refresh_at REAL NOT NULL DEFAULT 0,
    model TEXT,
    error_code TEXT,
    updated_at REAL NOT NULL
);
CREATE TABLE chatgpt_pairing (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL UNIQUE REFERENCES session(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL UNIQUE,
    nonce TEXT NOT NULL,
    expires_at REAL NOT NULL,
    claimed INTEGER NOT NULL DEFAULT 0,
    connection_id TEXT
);
CREATE TABLE chatgpt_import (
    import_id TEXT PRIMARY KEY REFERENCES import_draft(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    connection_id TEXT NOT NULL
);
