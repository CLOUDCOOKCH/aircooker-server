CREATE TABLE recipe_idea_request (
    id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    request TEXT,
    state TEXT NOT NULL CHECK(state IN ('queued','running','ready','failed','expired')),
    recipes TEXT,
    error_code TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX recipe_idea_retention ON recipe_idea_request(state, updated_at);
