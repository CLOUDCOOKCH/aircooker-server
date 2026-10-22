CREATE TABLE suggestion_application (
 id TEXT PRIMARY KEY, device_id TEXT NOT NULL REFERENCES device(id),
 fingerprint TEXT NOT NULL, result TEXT NOT NULL, created_at REAL NOT NULL
);
