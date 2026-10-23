CREATE TABLE food_profile (
 id INTEGER PRIMARY KEY CHECK(id=1),
 revision INTEGER NOT NULL CHECK(revision>=0),
 payload TEXT NOT NULL
);
-- Existing installations keep their current first-run experience. The picker remains reachable.
INSERT INTO food_profile
SELECT 1,0,json_object('likes',json('[]'),'dislikes',json('[]'),
 'pantry_setup_done',json(CASE WHEN EXISTS(SELECT 1 FROM household) THEN 'true' ELSE 'false' END),
 'taste_setup_done',json('false'));
CREATE TABLE food_profile_receipt (
 id TEXT PRIMARY KEY,
 device_id TEXT NOT NULL REFERENCES device(id),
 fingerprint TEXT NOT NULL,
 result TEXT NOT NULL,
 created_at REAL NOT NULL
);
