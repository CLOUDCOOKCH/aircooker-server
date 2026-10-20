CREATE TABLE recipe_media (
 id TEXT PRIMARY KEY, content_type TEXT NOT NULL CHECK(content_type='image/jpeg'),
 sha256 TEXT NOT NULL, source_sha256 TEXT NOT NULL,
 byte_count INTEGER NOT NULL CHECK(byte_count>0 AND byte_count<=1048576),
 width INTEGER NOT NULL CHECK(width>0 AND width<=2048),
 height INTEGER NOT NULL CHECK(height>0 AND height<=2048),
 data BLOB NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX media_created ON recipe_media(created_at);
