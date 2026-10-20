CREATE TABLE household (
 id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL, timezone TEXT NOT NULL,
 language TEXT NOT NULL CHECK(language IN ('en','de')), username TEXT NOT NULL,
 password_hash TEXT NOT NULL, instance_id TEXT NOT NULL UNIQUE
);
CREATE TABLE device (id TEXT PRIMARY KEY, last_seen REAL NOT NULL);
CREATE TABLE session (
 id TEXT PRIMARY KEY, device_id TEXT NOT NULL REFERENCES device(id),
 access_hash TEXT NOT NULL UNIQUE, refresh_hash TEXT NOT NULL UNIQUE,
 access_expires REAL NOT NULL, refresh_expires REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE refresh_history (token_hash TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES session(id));
CREATE TABLE rate_limit (key TEXT PRIMARY KEY, count INTEGER NOT NULL, resets REAL NOT NULL);
CREATE TABLE entity (
 kind TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL, deleted INTEGER NOT NULL,
 payload TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(kind,id)
);
CREATE TABLE change_log (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, entity_id TEXT NOT NULL,
 deleted INTEGER NOT NULL, payload TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX change_entity ON change_log(kind,entity_id,sequence);
CREATE TABLE mutation (
 id TEXT PRIMARY KEY, device_id TEXT NOT NULL REFERENCES device(id), fingerprint TEXT NOT NULL,
 result TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE background_job (
 id TEXT PRIMARY KEY, kind TEXT NOT NULL, dedupe_key TEXT NOT NULL UNIQUE,
 payload TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('queued','running','done','failed')),
 attempts INTEGER NOT NULL DEFAULT 0, available_at REAL NOT NULL, lease_until REAL,
 lease_token TEXT, generation INTEGER NOT NULL DEFAULT 1, claimed_generation INTEGER,
 error_code TEXT, created_at REAL NOT NULL
);
CREATE INDEX runnable_jobs ON background_job(state,available_at,lease_until);
CREATE TABLE import_draft (
 id TEXT PRIMARY KEY, source_url TEXT, source_platform TEXT NOT NULL,
 state TEXT NOT NULL, recipe TEXT, warnings TEXT NOT NULL, error_code TEXT,
 confirmed_recipe_id TEXT, created_at REAL NOT NULL
);
CREATE TABLE bring_owned_item (
 period TEXT NOT NULL, requirement_id TEXT NOT NULL, list_id TEXT NOT NULL,
 item_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, spec TEXT NOT NULL,
 state TEXT NOT NULL, applied_spec TEXT, reconciled_at REAL,
 PRIMARY KEY(period,requirement_id,list_id)
);
CREATE TABLE audit_event (id INTEGER PRIMARY KEY, code TEXT NOT NULL, created_at REAL NOT NULL);
