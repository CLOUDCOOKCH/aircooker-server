ALTER TABLE import_draft ADD COLUMN request_fingerprint TEXT CHECK(request_fingerprint IS NULL OR length(request_fingerprint)=64);
ALTER TABLE import_draft ADD COLUMN finished_at REAL CHECK(finished_at IS NULL OR finished_at>=0);
CREATE INDEX import_finished ON import_draft(state,finished_at);
CREATE INDEX session_expiry ON session(refresh_expires);
CREATE INDEX audit_age ON audit_event(created_at);
