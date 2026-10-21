CREATE TABLE push_subscription (
 id TEXT PRIMARY KEY,
 device_id TEXT NOT NULL UNIQUE REFERENCES device(id),
 session_id TEXT NOT NULL REFERENCES session(id),
 endpoint_hash TEXT NOT NULL UNIQUE,
 credentials TEXT NOT NULL,
 preferences TEXT NOT NULL,
 enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
 language TEXT NOT NULL CHECK(language IN ('en','de')),
 last_success REAL,
 error_code TEXT,
 updated_at REAL NOT NULL
);
CREATE TABLE push_delivery (
 subscription_id TEXT NOT NULL REFERENCES push_subscription(id) ON DELETE CASCADE,
 planned_date TEXT NOT NULL,
 category TEXT NOT NULL CHECK(category IN ('breakfast','lunch','dinner')),
 accepted_at REAL NOT NULL,
 PRIMARY KEY(subscription_id,planned_date,category)
);
