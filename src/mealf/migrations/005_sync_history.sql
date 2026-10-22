ALTER TABLE change_log ADD COLUMN commit_token TEXT;
UPDATE change_log SET commit_token=lower(hex(randomblob(16))) WHERE commit_token IS NULL;
CREATE UNIQUE INDEX change_commit_token ON change_log(commit_token);
