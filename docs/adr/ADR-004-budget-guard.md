# ADR-004: Budget Guard

## Status

Accepted.

## Context

The review agent can fan out to multiple LLM calls per pull request. Without cost controls, a provider issue, prompt regression, retry loop, or unusually large PR can create runaway spend.

Cost control must happen before the LLM call, not only after cost is recorded.

## Decision

Add a BudgetGuard that checks configured spend limits before every LLM call.

The guard reads current spend from event-derived rollups when available and from a direct event query as fallback. If the configured budget is exceeded, the guard blocks the LLM call and records a decision event.

Initial limits:

- daily LLM budget in USD
- optional per-review budget
- optional per-agent budget

## Consequences

Positive:

- Spend is bounded before new cost is incurred.
- Cost decisions are auditable.
- Model routing can use budget state later.

Negative:

- Reviews may be incomplete when the budget is exhausted.
- Rollup freshness must be understood so the guard does not undercount.

## Failure Behavior

If the budget backend is unavailable:

- production should fail closed for non-critical automated review
- local development and tests may use explicit fake budget state

The failure mode must be visible in `agent_events`.

