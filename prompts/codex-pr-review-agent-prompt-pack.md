# Codex Prompt Pack: AI Pull-Request Review Agent

Use these prompts as sequential Codex tasks. Each phase should leave the repo green before the next begins. The project target is a production-minded modular monolith for an AI PR review agent:

GitHub webhook -> FastAPI ingress -> Redis/ARQ queue -> LangGraph orchestrator -> four specialist review agents -> aggregator -> human approval gate -> GitHub review post, with one Tiger Cloud / Postgres-compatible data spine for memory, truth, events, rollups, and audit.

## Global Build Rules

Paste this context at the top of every phase prompt unless the task already has the codebase context:

```text
You are building a production-grade AI pull-request review agent.

Core architecture:
- Backend: Python FastAPI modular monolith.
- Queue: Redis + ARQ.
- Workflow: LangGraph behind a narrow workflow engine interface.
- Agents: security, quality, tests, docs.
- Output contract: structured Finding objects with severity, category, file/line, confidence, rationale, and suggestion.
- Data spine: Tiger Cloud / Postgres-compatible DB using relational tables, pgvector/pgvectorscale for code_chunks, Timescale hypertables for agent_events, and continuous aggregates for cost/health.
- Frontend: Next.js dashboard for reviews, traces, HITL queue, and economics.
- Human gate: auto-post confident non-critical reviews; route low-confidence or CRITICAL findings to human approval.
- Reliability: idempotency, retries, timeouts, circuit breakers, dead-letter handling, and auditability.

Engineering constraints:
- Prefer simple, typed, testable code.
- Keep modules inward-facing and loosely coupled.
- Do not call provider SDKs directly from business logic; wrap them.
- Every phase must include focused tests or smoke checks.
- Preserve a clean README and .env.example as the system evolves.
- Do not implement unrelated polish or speculative scale-outs unless required by the phase.
```

## Phase 0 - Product Contract and ADR Skeleton

```text
Create the initial project skeleton for the AI PR review agent.

Deliver:
- A monorepo-style structure with backend/, frontend/, scripts/, docs/, and migrations/.
- docs/PRODUCT_CONTRACT.md describing trigger, output, autonomy level, Finding contract, HITL rules, and non-goals.
- docs/adr/ADR-001-workflow-engine.md choosing LangGraph behind an interface, with Temporal as a future alternative.
- docs/adr/ADR-002-modular-monolith.md describing module boundaries and dependency rules.
- docs/adr/ADR-003-one-data-spine.md describing Tiger Cloud/Postgres as memory + truth + time spine, with Redis retained for queueing.
- docs/adr/ADR-004-budget-guard.md describing cost caps and pre-LLM blocking.
- Root README.md with local dev overview and phase roadmap.
- .gitignore and .env.example with placeholders only.

Acceptance:
- The repo structure is coherent.
- ADRs are specific enough to guide implementation.
- No secrets are committed.
- README explains how later phases fit together.
```

## Phase 1 - Backend Foundation

```text
Implement the backend foundation.

Deliver:
- backend/ Python package with FastAPI app factory.
- Configuration loading from environment using typed settings.
- Health endpoint.
- Common exception types.
- Structured logging setup.
- Pytest configuration and first backend tests.
- Dependency boundaries matching ADR-002.

Suggested modules:
- backend/app/main.py
- backend/app/config.py
- backend/app/core/exceptions.py
- backend/app/observability/logging.py
- backend/tests/

Acceptance:
- `pytest` passes.
- `uvicorn` or equivalent can start the app locally.
- `/health` returns a stable JSON response.
- Settings fail clearly when required production values are missing, but allow test defaults.
```

## Phase 2 - Data Models and Finding Contract

```text
Define the core domain models and schemas.

Deliver:
- Pydantic models for Finding, Review, WebhookEvent, AgentType, Severity, ReviewStatus, HITLStatus.
- Finding fields: id, review_id, agent_type, severity, category, summary, file_path, line_start, line_end, suggestion, confidence, rationale, evidence, created_at.
- Validation rules for confidence range, severity ordering, file/line requirements, and allowed agent types.
- Serialization tests for stable JSON output.
- Docs showing an example review payload.

Acceptance:
- Tests cover valid and invalid Finding payloads.
- The contract can be imported by agents, aggregator, API, and persistence modules without circular imports.
```

## Phase 3 - Database Schema and Repository Layer

```text
Implement the database schema and repository layer for the relational truth lane.

Deliver:
- Async Postgres connection setup.
- SQLAlchemy or SQLModel models for PR review records, finding records, HITL reviews, HITL feedback, webhook deliveries, and idempotency records.
- Initial migration script.
- Repository classes for creating reviews, saving findings, recording HITL decisions, checking idempotency, and fetching review details.
- Tests using a test database strategy or isolated repository fakes if a DB is unavailable.

Acceptance:
- Migration is idempotent.
- Repository tests verify create/read/update paths.
- No business logic depends directly on ORM session internals.
```

## Phase 4 - GitHub Webhook Ingress

```text
Build the GitHub webhook receiver.

Deliver:
- FastAPI route for GitHub pull_request webhooks.
- HMAC-SHA256 signature verification using GITHUB_WEBHOOK_SECRET.
- Payload parsing into WebhookEvent.
- Idempotency using X-GitHub-Delivery.
- Immediate enqueue call placeholder or interface.
- Tests for valid signature, invalid signature, duplicate delivery, unsupported event, and opened/synchronize/reopened PR actions.

Acceptance:
- Endpoint returns quickly and never runs review work inline.
- Duplicate webhook delivery is acknowledged without enqueuing duplicate work.
- Invalid signatures are rejected.
```

## Phase 5 - Queue Worker with Redis + ARQ

```text
Implement the Redis + ARQ job queue.

Deliver:
- Queue abstraction used by webhook ingress.
- ARQ worker entrypoint.
- Review job payload schema.
- Job enqueue from webhook route.
- Worker handler that records job start and calls a placeholder workflow engine.
- Retry/backoff settings and dead-letter strategy.
- Tests for enqueue payload shape and idempotent worker behavior where feasible.

Acceptance:
- Local worker can start.
- Webhook enqueues a review job.
- Worker logs/records job lifecycle.
- Queue code is isolated from review business logic.
```

## Phase 6 - Workflow Engine Interface

```text
Create the workflow orchestration abstraction.

Deliver:
- backend/app/core/workflow_engine.py with run, resume, get_state methods.
- Typed workflow input and state objects.
- Placeholder implementation that executes deterministic stub nodes.
- Tests proving the app imports only the interface outside the orchestrator package.
- Documentation explaining how LangGraph will plug in next.

Acceptance:
- Worker can call the workflow engine interface.
- No outer module imports LangGraph directly.
- State is serializable.
```

## Phase 7 - LangGraph Orchestrator

```text
Implement the LangGraph workflow.

Deliver:
- LangGraph implementation of WorkflowEngine.
- StateGraph with nodes: build_context, security_agent, quality_agent, tests_agent, docs_agent, aggregate, route_result.
- Parallel fan-out to four specialist nodes.
- Checkpointing configured with Redis or a local fallback for tests.
- Node-level timeouts.
- Tests proving all four agents run and aggregator waits for all completed outputs.

Acceptance:
- Workflow can run end-to-end with stub agents.
- Fan-out is parallel or modeled as parallel by LangGraph.
- Crashes/timeouts have clear error states.
- The interface remains stable.
```

## Phase 8 - Observability Event Spine

```text
Build the event emission layer.

Deliver:
- agent_events schema migration as a Timescale hypertable if extensions are available, with graceful local fallback.
- emit_agent_event(review_id, agent, event_type, payload, cost, latency, confidence, outcome).
- Span context support with span_id and parent_span.
- Instrument workflow nodes and worker lifecycle.
- Repository/query function to reconstruct a trace ordered by timestamp.
- Tests for event emission and trace ordering.

Acceptance:
- Every workflow run emits span.start/span.end and decision events.
- Event writing failure does not crash low-risk local tests, but production behavior is explicit.
- Trace reconstruction uses a single ordered query.
```

## Phase 9 - LLM Client and Prompt Registry

```text
Implement the LLM abstraction and prompt registry.

Deliver:
- LLM client wrapper with structured output support.
- Prompt registry with versioned templates for security, quality, tests, docs, and aggregator.
- Model routing interface.
- Token/cost accounting hooks into agent_events.
- BudgetGuard check before any LLM call.
- Tests using fake LLM responses.

Acceptance:
- Agents will depend on the LLM wrapper, not raw provider SDKs.
- Prompt versions are recorded in event payloads.
- BudgetGuard can block calls before cost is incurred.
```

## Phase 10 - Code Ingestion and Memory Schema

```text
Implement the code memory lane.

Deliver:
- code_chunks schema with repo, path, symbol, chunk_index, content, embedding, token_count, updated_at, and content_tsv where supported.
- repo_file_index freshness table.
- File ingestion pipeline that chunks source files, skips ignored/binary files, computes content hashes, and upserts changed chunks.
- Embedder abstraction with fake embedder for tests.
- Migration for vector indexes with safe fallback when pgvector/pgvectorscale is unavailable locally.
- Tests for chunking, hashing, and upsert behavior.

Acceptance:
- Re-running ingestion does not duplicate chunks.
- Changed files are re-embedded; unchanged files are skipped.
- Local tests can run without real Tiger Cloud credentials.
```

## Phase 11 - Hybrid Retrieval

```text
Build the context retriever used by agents.

Deliver:
- Vector search over code_chunks.
- Full-text/keyword search over code_chunks.
- Reciprocal rank fusion merge.
- top-k retrieval API that accepts repo, diff text, changed files, and agent type.
- Evidence objects that include path, symbol, content excerpt, rank, and retrieval method.
- Tests using seeded fake chunks.

Acceptance:
- Exact identifiers are found through keyword search.
- Semantically similar chunks are found through vector search or fake vector scoring in tests.
- Merged results are deterministic.
- Retrieved evidence can be attached to findings and event payloads.
```

## Phase 12 - Specialist Agent Base Class

```text
Implement the shared specialist agent framework.

Deliver:
- BaseReviewAgent with BudgetGuard check, retrieval call, prompt construction, LLM structured output call, validation, event emission, and error handling.
- AgentResult type containing findings, confidence, evidence, errors, and metadata.
- Per-agent timeout and retry policy.
- Tests using fake retriever and fake LLM.

Acceptance:
- Base class handles common mechanics once.
- Agent-specific logic is limited to prompt/template and post-processing.
- Invalid LLM output is handled safely and recorded.
```

## Phase 13 - Four Specialist Agents

```text
Implement the four specialist agents.

Deliver:
- SecurityReviewAgent focused on exploitable risks, secrets, auth, injection, unsafe deserialization.
- QualityReviewAgent focused on correctness, edge cases, maintainability, complexity, API misuse.
- TestsReviewAgent focused on missing coverage, brittle tests, edge cases, regression risk.
- DocsReviewAgent focused on public API docs, outdated comments, missing rationale, reader clarity.
- Prompt templates for each.
- Unit tests proving each agent maps structured LLM responses into Finding objects.

Acceptance:
- Each agent returns only findings within its concern.
- Each finding includes rationale, confidence, and evidence when available.
- Agents can return no findings without failure.
```

## Phase 14 - Aggregator and HITL Routing

```text
Implement the aggregator and routing decision.

Deliver:
- Aggregator that merges findings from all four agents.
- Deduplication by file, line range, category, and semantic similarity where feasible.
- Severity and confidence scoring.
- Rules:
  - auto-post if confidence >= configured threshold and no CRITICAL findings
  - route to human approval if below threshold
  - escalate if any CRITICAL finding
- Persist Review and Finding records.
- Create HITL review records when needed.
- Tests for merge, dedup, severity precedence, confidence scoring, and routing.

Acceptance:
- Aggregator is deterministic.
- Duplicate findings do not spam the PR.
- Routing reason is recorded.
```

## Phase 15 - GitHub Review Posting

```text
Implement GitHub review posting.

Deliver:
- GitHub client wrapper for PR details, changed files/diff retrieval, posting reviews, and posting inline comments.
- Authentication through GitHub App credentials.
- Review formatter from structured findings to GitHub review comments.
- Idempotent post behavior to avoid duplicate reviews.
- Retry and circuit breaker around GitHub API calls.
- Tests with mocked GitHub API.

Acceptance:
- Confident reviews can be posted to GitHub.
- Low-confidence or critical reviews are not posted automatically.
- API failures are retried and eventually recorded as failed without duplicate posts.
```

## Phase 16 - Human Approval Queue API

```text
Build the HITL backend.

Deliver:
- API endpoints to list pending reviews, inspect review details, approve posting, reject, edit summary, escalate, and resolve disputes.
- Feedback capture for accepted/rejected findings.
- Audit events for every human decision.
- RBAC dependency stubs or implementation.
- Tests for approval, rejection, dispute, and feedback flows.

Acceptance:
- A low-confidence review can be approved and then posted to GitHub.
- Human decisions are persisted and auditable.
- Feedback is stored without immediately poisoning future behavior.
```

## Phase 17 - Economics and Rollups

```text
Implement cost and health reporting.

Deliver:
- Continuous aggregate migrations for agent_health_1m and pr_cost_hourly where Timescale is available.
- Local fallback views or repository fakes for tests.
- CostRepository for per-agent cost, p95 latency, token usage, rejection rate, and per-PR cost.
- BudgetGuard wired to read daily spend before LLM calls.
- API endpoints for economics dashboard.
- Tests for budget blocking and cost queries.

Acceptance:
- BudgetGuard hard-blocks before LLM call when cap is exceeded.
- Cost APIs return stable JSON.
- Rollup migrations are idempotent.
```

## Phase 18 - Frontend Dashboard Shell

```text
Create the Next.js frontend foundation.

Deliver:
- Next.js app with routes for reviews, review detail, trace viewer, HITL queue, and economics.
- API client layer.
- App navigation and loading/error states.
- Clean operational UI, not a marketing landing page.
- Mock data mode for local frontend development.

Acceptance:
- Frontend starts locally.
- All main routes render.
- UI is dense, readable, and useful for a developer/operator.
- No page depends on production credentials.
```

## Phase 19 - Frontend Review, Trace, HITL, and Economics Views

```text
Build the usable frontend views.

Deliver:
- Reviews list with status, repo, PR number, confidence, cost, created time.
- Review detail with findings grouped by agent and severity.
- Trace viewer reconstructing agent_events in timestamp order.
- HITL queue with approve/reject/escalate actions.
- Economics page showing cost by agent, p95 latency, token usage, and budget state.
- Empty, loading, error, and refresh states.

Acceptance:
- Operators can inspect why a review was produced.
- Operators can approve or reject HITL reviews.
- Cost and latency views are understandable at a glance.
- UI text does not overlap on mobile or desktop.
```

## Phase 20 - Security Hardening

```text
Harden the system security posture.

Deliver:
- Threat model document.
- Prompt injection guard for retrieved repo content and PR text.
- Secret masking in logs, events, traces, and frontend.
- RBAC enforcement for dashboard/API.
- GitHub webhook replay protection if feasible.
- Tool capability scoping for any sandboxed operations.
- Tests for masking, unauthorized access, invalid signatures, and injection guard behavior.

Acceptance:
- Secrets do not appear in logs/events/API responses.
- Protected endpoints require auth/RBAC.
- Retrieved code is treated as untrusted input in prompts.
```

## Phase 21 - Reliability and Fault Injection

```text
Implement and test reliability mechanics end-to-end.

Deliver:
- Retry utilities with exponential backoff.
- Circuit breaker abstraction for LLM and GitHub calls.
- Per-node workflow timeouts.
- Dead-letter handling for failed jobs.
- Idempotency tests across webhook, worker, aggregator, and GitHub posting.
- Fault injection tests for LLM timeout, GitHub timeout, DB write failure, retrieval failure, and one hung specialist.

Acceptance:
- The system degrades to slower-but-correct or explicit failure.
- One failed specialist does not deadlock the aggregator forever.
- Duplicate webhooks do not create duplicate reviews/comments.
```

## Phase 22 - Evaluation Harness

```text
Build the review quality evaluation system.

Deliver:
- Golden dataset format for sample PR diffs, expected findings, and acceptable findings.
- Evaluation runner.
- LLM-as-judge wrapper behind an interface.
- Metrics: precision-ish score, missed criticals, false positives, severity calibration, rationale quality.
- Regression gate for CI.
- Example golden cases for security, quality, tests, and docs.

Acceptance:
- Evaluation runs locally with fake judge mode.
- CI can fail if review quality regresses beyond threshold.
- Metrics are recorded clearly enough to compare prompt/model versions.
```

## Phase 23 - CI/CD for AI Changes

```text
Set up CI/CD for the project and AI-specific changes.

Deliver:
- CI workflow running backend tests, frontend tests/lint, migrations check, and evaluation harness in fake/offline mode.
- Prompt version tracking.
- Canary configuration document for model/prompt rollout.
- Release checklist.
- Developer docs for adding a new agent or prompt version.

Acceptance:
- CI runs without real production secrets.
- Prompt/model changes are reviewable and gated.
- The repo documents how to ship safely.
```

## Phase 24 - End-to-End Local Demo

```text
Wire an end-to-end local demo path.

Deliver:
- Script or CLI command to simulate a GitHub pull_request webhook from a fixture.
- Fixture repo/diff with known issues.
- Local fake LLM mode that returns deterministic findings.
- Full flow: webhook -> queue -> workflow -> agents -> aggregator -> HITL or post stub -> dashboard.
- README demo instructions.

Acceptance:
- A new developer can run the demo without external credentials.
- The demo produces a review record, findings, events, and dashboard-visible output.
- The same path can switch to real providers when credentials are configured.
```

## Phase 25 - Production Readiness Pass

```text
Perform a production readiness pass.

Deliver:
- Review all modules for boundary violations, missing tests, secret leakage, and operational gaps.
- Update README, .env.example, ADRs, and deployment docs.
- Add any missing smoke tests.
- Verify startup order for DB, Redis, backend, worker, and frontend.
- Produce docs/PRODUCTION_READINESS.md with known risks, scale limits, and next decisions.

Acceptance:
- Backend tests pass.
- Frontend checks pass.
- Local demo passes.
- Documentation accurately reflects the implemented system.
- Known risks are explicit rather than hidden.
```

## Optional Phase 26 - Deployable Infrastructure

```text
Add deployable infrastructure for the project.

Deliver:
- Dockerfiles for backend, worker, and frontend.
- docker-compose for local dependencies.
- Deployment guide for Railway or equivalent.
- Environment variable checklist.
- Health checks and worker process commands.
- Migration run instructions.

Acceptance:
- The project can run through docker-compose locally.
- Production deployment docs are precise enough to follow.
- Secrets remain environment-only.
```

## Recommended Codex Execution Pattern

For each phase, start a new Codex task or continue in the same repo with this instruction:

```text
Before editing, inspect the current repo and summarize what already exists. Then implement only this phase. Keep changes scoped. Add or update tests. Run the relevant checks. End with:
- files changed
- tests run
- any blockers
- exact next recommended phase
```

Do not start multiple later phases in the same task unless the current phase is already green.

