# ADR-002: Modular Monolith

## Status

Accepted.

## Context

The project has many concerns: GitHub ingress, queueing, orchestration, retrieval, LLM calls, agent logic, aggregation, HITL workflows, observability, economics, and frontend operations.

Splitting these into services too early would add deployment, networking, tracing, and transaction complexity before the core behavior is proven.

## Decision

Build a modular monolith first.

The backend is one deployable application with explicit internal modules and inward-facing dependencies. Modules expose small interfaces and avoid importing implementation details from outer layers.

Expected backend modules:

- `agents`
- `api`
- `auth`
- `core`
- `data`
- `database`
- `economics`
- `evaluation`
- `hitl`
- `integrations`
- `job_queue`
- `memory`
- `models`
- `observability`
- `orchestrator`
- `prompts`
- `reliability`
- `security`
- `tools`
- `webhook_receiver`

## Dependency Rule

`core` and `models` must remain low-level and reusable. Outer modules depend inward through interfaces. Cross-cutting behavior such as observability is injected through wrappers, middleware, or explicit event emitters.

Examples:

- API routes may call repositories and services.
- Agents may call retriever and LLM interfaces.
- Agents must not call raw database sessions, raw provider SDKs, or web framework request objects.
- Business logic must not import LangGraph directly.

## Consequences

Positive:

- One process is easier to run and debug.
- Transactions and local development remain simpler.
- Module boundaries can later become service boundaries if measured pressure requires it.

Negative:

- Boundary discipline is cultural and test-enforced, not physically guaranteed by network boundaries.
- A careless import can create coupling unless checked.

## Extraction Triggers

Consider extracting a module when:

- queue ingress and worker scaling profiles diverge sharply
- retrieval load requires separate deployment or hardware
- frontend/API/operator traffic must scale independently
- a module has independent ownership and operational needs

