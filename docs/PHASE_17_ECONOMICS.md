# Phase 17: Economics and Rollups

Phase 17 adds cost reporting.

## Backend

`CostRepository` reads `agent_events` and provides:

- daily LLM spend
- cost by agent
- token usage
- p95 latency
- per-PR cost

`BudgetGuard` can now use the event-backed repository.

## API

- `GET /economics/agents`
- `GET /economics/budget`

The API uses an injectable service so tests and local demos can run without production DB credentials.

## SQL

The migration adds `agent_health_1m` and `pr_cost_hourly` materialized views for production rollups.

