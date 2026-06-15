-- Adds the "new" value to the applicationstatus enum type.
-- create_all() does not alter existing enum types, so this must be run manually
-- if job_applications already exists in the database.

ALTER TYPE applicationstatus ADD VALUE IF NOT EXISTS 'new' BEFORE 'applied';
