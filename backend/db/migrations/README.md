# DB Migrations

This app uses SQLAlchemy's `Base.metadata.create_all()` on startup (see
`app/main.py`), which **creates new tables automatically** but **never alters
existing tables** (e.g. adding/renaming columns on a table that already
exists).

Whenever a model change adds/changes columns on a table that may already
exist in a deployed database, add a numbered SQL script here describing the
change, and run it manually against the Neon database (SQL Editor or
DBeaver) before/after deploying the new code.

New tables do not need a script — `create_all()` handles them on next
startup/deploy.

## Scripts

- `0001_add_user_id_to_resumes_and_topics.sql` — adds the `user_id` column
  (and index) to `resumes` and `topics`, needed after auth was added to a
  database that already had those tables.
- `0002_job_applications.sql` — reference DDL for the new `job_applications`
  and `application_questions` tables (created automatically by
  `create_all()`; kept here for documentation/manual recovery only).

## Running a script

In the Neon Console → SQL Editor (or DBeaver connected to the Neon DB), paste
and run the contents of the script.
