-- Reference DDL for the Job Application Tracker tables.
-- These are new tables, so create_all() creates them automatically on
-- startup/deploy. This script is kept for documentation/manual recovery only.

CREATE TABLE IF NOT EXISTS job_applications (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'applied',
    source VARCHAR(255),
    job_post_link VARCHAR(1000),
    job_portal_link VARCHAR(1000),
    poc VARCHAR(255),
    notes TEXT,
    practice_interview_done BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_job_applications_user_id ON job_applications (user_id);

CREATE TABLE IF NOT EXISTS application_questions (
    id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    ideal_answer TEXT,
    difficulty VARCHAR(50) NOT NULL DEFAULT 'medium',
    source VARCHAR(50) NOT NULL DEFAULT 'gemini',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
