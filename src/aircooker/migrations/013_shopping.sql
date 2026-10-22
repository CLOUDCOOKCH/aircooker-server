CREATE TABLE shopping_sync (
 slot INTEGER PRIMARY KEY CHECK(slot=1), period TEXT NOT NULL, list_id TEXT NOT NULL,
 completed_at REAL NOT NULL, manual_names TEXT NOT NULL
);
CREATE TABLE bring_probe (
 id TEXT PRIMARY KEY, list_id TEXT NOT NULL, configuration_hash TEXT NOT NULL,
 item_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, stage INTEGER NOT NULL DEFAULT 0,
 baseline TEXT, completed_at REAL, created_at REAL NOT NULL
);
