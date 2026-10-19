# Database setup

The backend uses PostgreSQL and pgvector for project-description retrieval.
The existing application tables (`users`, `chat`, `landscape_analyses`, and
article tables) must already exist. Install the pgvector extension on the
PostgreSQL server, then apply
[`001_project_rag_ideas.sql`](./001_project_rag_ideas.sql) before starting the
updated application. The application also requests
`CREATE EXTENSION IF NOT EXISTS vector` during startup; the database role must
be permitted to use that extension.

If `idea_generation_runs.request_payload` is missing, apply
[`002_idea_generation_request_payload.sql`](./002_idea_generation_request_payload.sql)
to the same database configured for the application, then restart the backend.
This migration is safe to rerun.

Apply
[`003_article_summary_chat_url_uniqueness.sql`](./003_article_summary_chat_url_uniqueness.sql)
to allow the same article URL in different chats while preventing duplicate
article rows within a chat. The application uses conflict-safe inserts to
reuse existing article summaries during repeated research.

The migration creates `vector(768)` to match the default
`RAG_EMBEDDING_DIMENSIONS=768`. If a different embedding dimension is
configured, update the migration's vector column dimension before applying it.
The same dimension must be used for the embedding model and its PostgreSQL
column.

RAG configuration is optional and can be set in the environment:

| Variable | Default | Purpose |
| --- | --- | --- |
| `RAG_EMBEDDING_MODEL` | `gemini-embedding-001` | Google GenAI embedding model |
| `RAG_EMBEDDING_DIMENSIONS` | `768` | Vector column and provider output size |
| `RAG_SIMILARITY_THRESHOLD` | `0.25` | Minimum cosine similarity |
| `RAG_RETRIEVAL_LIMIT` | `5` | Maximum retrieved project chunks |
| `RAG_MAX_CONTEXT_CHARACTERS` | `12000` | Retrieved context character budget |
| `RAG_CHUNK_SIZE` | `1500` | Project text chunk size |
| `RAG_CHUNK_OVERLAP` | `150` | Chunk overlap |

Embedding requests use the existing configured Google GenAI client and API
credentials. Project rows remain authoritative if indexing fails; use
`POST /projects/{project_id}/reindex` to retry indexing.
