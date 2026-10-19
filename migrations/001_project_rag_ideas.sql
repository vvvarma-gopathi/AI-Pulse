-- Run this migration before starting the application.
-- The application uses SQLAlchemy create_all for tables, but create_all
-- does not alter existing tables or install PostgreSQL extensions.
BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS projects (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name varchar(200) NOT NULL,
    description text NOT NULL,
    technologies jsonb NOT NULL DEFAULT '[]'::jsonb,
    goals jsonb NOT NULL DEFAULT '[]'::jsonb,
    capabilities jsonb NOT NULL DEFAULT '[]'::jsonb,
    limitations jsonb NOT NULL DEFAULT '[]'::jsonb,
    status varchar(50) NOT NULL DEFAULT 'active',
    indexing_status varchar(20) NOT NULL DEFAULT 'pending',
    updated_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id);

CREATE TABLE IF NOT EXISTS project_document_chunks (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    document_type varchar(40) NOT NULL DEFAULT 'user_project',
    source_id uuid NOT NULL,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    embedding vector(768) NOT NULL,
    updated_at timestamptz NOT NULL,
    CONSTRAINT uq_project_document_chunk UNIQUE(project_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS ix_project_chunks_owner_type
    ON project_document_chunks(user_id, document_type);
CREATE INDEX IF NOT EXISTS ix_project_chunks_embedding_cosine
    ON project_document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS idea_generation_runs (
    id uuid PRIMARY KEY,
    landscape_analysis_id uuid NOT NULL
        REFERENCES landscape_analyses(id) ON DELETE CASCADE,
    chat_id uuid NOT NULL,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    generation_mode varchar(50) NOT NULL,
    request_id uuid,
    request_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status varchar(20) NOT NULL DEFAULT 'completed',
    retrieval_status varchar(40) NOT NULL DEFAULT 'completed',
    failure_code varchar(50),
    project_ids_used jsonb NOT NULL DEFAULT '[]'::jsonb,
    supporting_article_references jsonb NOT NULL DEFAULT '[]'::jsonb,
    model_name varchar(150) NOT NULL,
    prompt_version varchar(50) NOT NULL DEFAULT 'idea-generation-v1',
    overall_summary text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE idea_generation_runs
    ADD COLUMN IF NOT EXISTS user_id uuid REFERENCES users(id) ON DELETE CASCADE;
UPDATE idea_generation_runs AS run
SET user_id = owner.id
FROM landscape_analyses AS analysis
JOIN chat AS research_chat ON research_chat.id = analysis.chat_id
JOIN users AS owner ON owner.user_name = research_chat.user_name
WHERE run.landscape_analysis_id = analysis.id
  AND run.user_id IS NULL;
ALTER TABLE idea_generation_runs
    ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE idea_generation_runs
    ADD COLUMN IF NOT EXISTS project_ids_used jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE idea_generation_runs
    ADD COLUMN IF NOT EXISTS supporting_article_references jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE idea_generation_runs
    ADD COLUMN IF NOT EXISTS request_id uuid;
ALTER TABLE idea_generation_runs
    ADD COLUMN IF NOT EXISTS request_payload jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE idea_generation_runs
    ADD COLUMN IF NOT EXISTS status varchar(20) NOT NULL DEFAULT 'completed';
ALTER TABLE idea_generation_runs
    ADD COLUMN IF NOT EXISTS retrieval_status varchar(40) NOT NULL DEFAULT 'completed';
ALTER TABLE idea_generation_runs
    ADD COLUMN IF NOT EXISTS failure_code varchar(50);
CREATE UNIQUE INDEX IF NOT EXISTS uq_idea_generation_user_request
    ON idea_generation_runs(user_id, request_id)
    WHERE request_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS project_ideas (
    id uuid PRIMARY KEY,
    generation_id uuid NOT NULL
        REFERENCES idea_generation_runs(id) ON DELETE CASCADE,
    title varchar(150) NOT NULL,
    problem text NOT NULL,
    feasibility_score integer NOT NULL,
    potential_impact_score integer NOT NULL,
    novelty_score integer NOT NULL,
    details jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_project_ideas_generation_id
    ON project_ideas(generation_id);
CREATE INDEX IF NOT EXISTS ix_project_ideas_generation_title
    ON project_ideas(generation_id, title);

COMMIT;
