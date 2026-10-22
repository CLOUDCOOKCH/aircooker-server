ALTER TABLE import_draft ADD COLUMN recognized_text TEXT CHECK(recognized_text IS NULL OR length(recognized_text)<=100000);
