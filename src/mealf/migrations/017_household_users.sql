CREATE TABLE household_user (
 id TEXT PRIMARY KEY,
 username TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','user')),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
INSERT INTO household_user(id,username,password_hash,role)
 SELECT instance_id,username,password_hash,'admin' FROM household;
ALTER TABLE session ADD COLUMN user_id TEXT REFERENCES household_user(id);
UPDATE session SET user_id=(SELECT instance_id FROM household);
