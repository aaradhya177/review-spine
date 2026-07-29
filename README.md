# Review Spine

Review Spine is a production-minded AI pull-request review agent. It is designed as a modular monolith that reviews GitHub pull requests through four grounded specialist agents, merges their structured findings, and routes the result through a confidence-weighted human approval gate.

## Target Architecture

```text
GitHub webhook
  -> FastAPI ingress
  -> Redis / ARQ queue
  -> LangGraph workflow engine
  -> security + quality + tests + docs agents
  -> aggregator
  -> human approval gate or GitHub review post
```

One durable Tiger Cloud / Postgres-compatible data spine carries:

- semantic code memory through `pgvector` / `pgvectorscale`
- review truth through relational tables
- time-ordered proof through Timescale hypertables
- cost and health summaries through continuous aggregates

Redis remains the short-lived queue and checkpoint-adjacent infrastructure.

## Repository Layout

```text
backend/      FastAPI app, worker, agents, orchestration, persistence
frontend/     Next.js dashboard for reviews, traces, HITL, and economics
docs/         product contract, ADRs, readiness docs
migrations/   database schema and extension setup
prompts/      Codex phase prompts and later agent prompt templates
scripts/      local dev, fixture, and smoke-test scripts
```

## Phase Roadmap

1. Product contract and ADR skeleton
2. Backend foundation
3. Domain models and Finding contract
4. Database schema and repository layer
5. GitHub webhook ingress
6. Redis + ARQ worker
7. Workflow engine interface
8. LangGraph orchestrator
9. Event spine
10. LLM client and prompt registry
11. Code ingestion and memory schema
12. Hybrid retrieval
13. Specialist agent base class
14. Four specialist agents
15. Aggregator and HITL routing
16. GitHub review posting
17. HITL API
18. Economics and rollups
19. Frontend dashboard shell
20. Frontend operational views
21. Security hardening
22. Reliability and fault injection
23. Evaluation harness
24. CI/CD for AI changes
25. End-to-end local demo
26. Production readiness pass
27. Optional deployable infrastructure

Each phase should leave the repo green before the next begins.

## Local Setup

This Phase 0 skeleton does not run an application yet. Backend, frontend, queue, and database commands will be added in later phases.

Copy `.env.example` to `.env` for local development once executable code exists. Keep real secrets out of source control.

## Current Status

Phase 0 defines why the system exists, what it produces, where humans stay in the loop, and which architecture decisions guide implementation.

Phase 1 adds the backend foundation: FastAPI app factory, typed settings, health endpoint, common exceptions, structured logging, and initial tests.

Phase 2 adds the shared domain contracts: `Finding`, `Review`, `WebhookEvent`, severity/status enums, validation rules, and an example JSON finding.

Phase 3 adds the relational truth lane: async SQLAlchemy setup, review/finding/HITL/webhook/idempotency ORM records, an idempotent SQL migration, and repository tests.

Phase 4 adds GitHub webhook ingress: HMAC verification, pull request payload parsing, delivery idempotency, supported action filtering, and enqueue handoff through a queue interface.

Phase 5 adds the Redis/ARQ queue path: stable review job IDs, an ARQ queue adapter, a worker entrypoint, placeholder workflow handoff, retry settings, and lifecycle recording for started/completed/failed jobs.

Phase 6 adds the shared workflow engine contract: serializable workflow input/state models, a `WorkflowEngine` protocol, and a deterministic stub engine used by the ARQ worker until LangGraph is wired in.

Run the current backend checks with:

```bash
python -m pytest
```

Run the worker after installing project dependencies and starting Redis:

```powershell
.\scripts\run_worker.ps1
```
