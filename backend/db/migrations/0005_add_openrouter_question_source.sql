-- Adds the 'openrouter' value to the questionsource enum for the new
-- OpenRouter provider option.
-- create_all() does not alter existing types, so this must be run manually.

ALTER TYPE questionsource ADD VALUE IF NOT EXISTS 'openrouter';
