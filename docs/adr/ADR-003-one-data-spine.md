# ADR-003: One Durable Data Spine

## Status

Accepted for initial implementation.

## Context

The agent needs three durable data shapes:

- semantic memory: code chunks and embeddings for retrieval
- truth: reviews, findings, GitHub IDs, HITL state, and feedback
- time: spans, LLM calls, tool calls, decisions, costs, latency, and outcomes

The reflexive design would use a vector database, a relational database, and a time-series database. That creates multiple connection pools, backups, query paths, and consistency boundaries.

## Decision

Use Tiger Cloud / Postgres-compatible storage as one durable data spine.

It carries:

- normal relational tables for review truth
- `pgvector` and `pgvectorscale` for `code_chunks`
- Timescale hypertables for `agent_events`
- continuous aggregates for cost, health, and dashboard rollups

Redis remains for ARQ queueing and short-lived workflow infrastructure. The decision is one durable data spine, not one tool for every workload.

## Consequences

Positive:

- One SQL query path for review truth, retrieved context, and event proof.
- Simpler backups, credentials, migrations, and operational reasoning.
- Cost ledger, trace viewer, and audit trail can share the same event rows.
- Retrieval evidence and findings can be joined through review identifiers.

Negative:

- Vector, relational, and time-series workloads may compete for database resources.
- Local development needs graceful fallback when extensions are unavailable.
- Future scale may require isolating workloads.

## Implementation Notes

Core tables and views:

- `code_chunks`
- `repo_file_index`
- `pr_review_records`
- `finding_records`
- `hitl_reviews`
- `hitl_feedback`
- `webhook_deliveries`
- `agent_events`
- `agent_health_1m`
- `pr_cost_hourly`

Migrations must be idempotent and extension-aware.

## Revisit Triggers

Revisit this decision if:

- vector recall or latency cannot meet review needs
- agent event volume harms transactional review operations
- continuous aggregate refreshes become expensive
- workload isolation becomes a production requirement

