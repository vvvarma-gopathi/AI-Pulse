-- Allow the same source article to be researched in multiple chats while
-- keeping article URLs unique within each chat.
BEGIN;

DROP INDEX IF EXISTS ix_article_summaries_url;

CREATE INDEX IF NOT EXISTS ix_article_summaries_url
    ON article_summaries(url);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_article_summaries_chat_url'
          AND conrelid = 'article_summaries'::regclass
    ) THEN
        ALTER TABLE article_summaries
            ADD CONSTRAINT uq_article_summaries_chat_url
            UNIQUE (chat_id, url);
    END IF;
END;
$$;

COMMIT;
