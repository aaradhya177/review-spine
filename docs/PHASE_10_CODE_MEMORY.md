# Phase 10: Code Memory

Phase 10 adds the ingestion side of the semantic memory lane.

## Schema

The production migration creates:

- `code_chunks`
- `repo_file_index`

`code_chunks.embedding` is defined as `VECTOR(256)` in SQL for Tiger/Postgres. The local ORM stores embeddings as JSON so SQLite tests can run without pgvector.

## Ingestion

`CodeIngestionService`:

- walks source files
- skips common generated/cache directories
- skips likely binary files
- hashes file content
- skips unchanged files
- chunks text by line groups
- embeds chunks through an injected embedder
- replaces chunks for changed files
- updates `repo_file_index`

## Embedder

`FakeEmbedder` gives deterministic vectors for tests. Real embedding provider wiring can replace the `Embedder` protocol later.

