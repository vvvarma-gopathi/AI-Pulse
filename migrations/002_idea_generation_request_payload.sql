-- Add the request payload column to existing idea-generation tables.
-- SQLAlchemy create_all does not add columns to tables that already exist.
BEGIN;

ALTER TABLE idea_generation_runs
    ADD COLUMN IF NOT EXISTS request_payload jsonb NOT NULL DEFAULT '{}'::jsonb;

COMMIT;
