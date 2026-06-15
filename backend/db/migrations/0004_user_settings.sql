-- Reference DDL for the user_settings table.
-- This is a new table, so create_all() creates it automatically on
-- startup/deploy. This script is kept for documentation/manual recovery only.

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    preferred_provider VARCHAR(50) NOT NULL DEFAULT 'gemini',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_user_settings_user_id ON user_settings (user_id);
