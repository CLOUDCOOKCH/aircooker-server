CREATE TABLE import_source_photo (
 import_id TEXT PRIMARY KEY REFERENCES import_draft(id) ON DELETE CASCADE,
 image_id TEXT NOT NULL REFERENCES recipe_media(id),
 source_url TEXT NOT NULL CHECK(length(source_url)<=2048)
);
