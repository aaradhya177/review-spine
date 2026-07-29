# Production Readiness

## Current Green Gates

- Backend unit tests pass locally.
- Frontend production build passes locally.
- Local webhook demo queues a review job.
- CI workflow runs backend tests and frontend build.

## Startup Order

1. Tiger/Postgres database
2. Redis
3. backend API
4. ARQ worker
5. frontend dashboard

## Implemented Surfaces

- GitHub webhook validation and idempotency
- queue abstraction and ARQ worker entrypoint
- workflow interface and orchestrator graph
- event spine
- prompt/LLM wrapper
- code ingestion and hybrid retrieval
- specialist agents and aggregator
- HITL and economics APIs
- frontend dashboard shell
- security and reliability primitives
- evaluation harness
- local webhook demo

## Known Risks

- Real GitHub App transport is not wired.
- Real provider SDK implementation is not wired.
- Repository-backed API dependencies are not globally configured.
- Local vector search is a test fallback, not production DiskANN.
- Frontend still uses mock data.
- `npm audit` reports high-severity advisories in the fresh Next dependency tree; do not force-upgrade without validating compatibility.
- Production auth is represented by an RBAC dependency hook, not an identity provider.

## Next Decisions

- Choose production hosting target.
- Wire authenticated GitHub transport.
- Wire OpenAI/provider implementation.
- Connect frontend API client to backend endpoints.
- Provision Tiger Cloud and run migrations.
- Decide whether to deploy as one process group or split API/worker/frontend.

