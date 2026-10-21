CREATE TABLE planning_preferences (
 id INTEGER PRIMARY KEY CHECK(id=1),
 revision INTEGER NOT NULL CHECK(revision>=0),
 payload TEXT NOT NULL
);
INSERT INTO planning_preferences VALUES (1,0,'{"categories":["dinner"],"allow_repeats":false,"servings":null,"use_leftovers":true}');
CREATE TABLE planning_preference_receipt (
 id TEXT PRIMARY KEY,
 device_id TEXT NOT NULL REFERENCES device(id),
 fingerprint TEXT NOT NULL,
 result TEXT NOT NULL,
 created_at REAL NOT NULL
);
CREATE TABLE suggestion_acceptance (
 recipe_id TEXT PRIMARY KEY REFERENCES recipe(id),
 count INTEGER NOT NULL CHECK(count BETWEEN 1 AND 1000000)
);
