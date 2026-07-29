CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS code_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo TEXT NOT NULL,
    path TEXT NOT NULL,
    symbol TEXT,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(256) NOT NULL,
    token_count INT,
    content_hash TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT code_chunks_unique_idx UNIQUE (repo, path, chunk_index)
);

CREATE INDEX IF NOT EXISTS ix_code_chunks_repo
    ON code_chunks (repo);

ALTER TABLE code_chunks
    ADD COLUMN IF NOT EXISTS content_tsv TSVECTOR
        GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

CREATE INDEX IF NOT EXISTS code_chunks_fts_idx
    ON code_chunks USING GIN (content_tsv);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_extension
        WHERE extname = 'vectorscale'
    ) THEN
        CREATE INDEX IF NOT EXISTS code_chunks_emb_idx
            ON code_chunks USING diskann (embedding vector_cosine_ops);
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS repo_file_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo TEXT NOT NULL,
    path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    last_indexed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT repo_file_index_unique_idx UNIQUE (repo, path)
);

CREATE INDEX IF NOT EXISTS ix_repo_file_index_repo
    ON repo_file_index (repo);

