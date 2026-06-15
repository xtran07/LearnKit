-- Adds user_id to resumes and topics for databases created before auth was added.
-- create_all() does not alter existing tables, so this must be run manually.

ALTER TABLE resumes ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);
ALTER TABLE topics ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

CREATE INDEX IF NOT EXISTS ix_resumes_user_id ON resumes (user_id);
CREATE INDEX IF NOT EXISTS ix_topics_user_id ON topics (user_id);
