# Phase 11: Hybrid Retrieval

Phase 11 adds the context retriever used by specialist agents.

## Search Lanes

`TigerMemoryClient` now supports:

- local vector scoring with cosine similarity over stored embeddings
- keyword scoring over chunk content and path

In production, these methods can be backed by `pgvectorscale`/DiskANN and Postgres full-text search.

## Fusion

`ContextRetriever` runs both lanes and merges them with reciprocal rank fusion. Returned evidence includes:

- path
- symbol
- content
- rank
- score
- method (`vector`, `keyword`, or both)

The retriever accepts repo, diff text, changed files, agent type, and top-k.

