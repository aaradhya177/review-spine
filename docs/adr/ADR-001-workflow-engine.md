# ADR-001: Workflow Engine

## Status

Accepted for initial implementation.

## Context

The review workflow needs to coordinate four specialist agents in parallel, persist state between steps, handle retries and timeouts, and route the final result through aggregation and human approval logic.

The system should start simple enough for fast iteration but avoid coupling the whole codebase to one orchestration library.

## Decision

Use LangGraph for the initial workflow engine. Hide it behind a narrow interface in `backend/app/core/workflow_engine.py` with these operations:

- `run(workflow_id, input)`
- `resume(workflow_id, state)`
- `get_state(workflow_id)`

Application code depends on the interface. LangGraph-specific code lives in the orchestrator module.

## Alternatives Considered

### Temporal

Temporal has stronger durability and mature distributed workflow guarantees. It is a good future option if workflow volume, cross-service coordination, or durability requirements outgrow LangGraph plus Redis checkpointing.

It is not selected initially because it adds operational weight before the workflow shape is proven.

### Hand-Written Orchestration

A manual fan-out/join implementation would reduce dependencies but would recreate workflow state, retries, timeouts, and failure handling poorly.

## Consequences

Positive:

- Fast local iteration.
- First-class LLM and graph workflow ergonomics.
- Natural fan-out and aggregation shape.
- Future engine swap is constrained to one implementation boundary.

Negative:

- LangGraph durability and scale characteristics must be measured.
- Some workflow behavior may require adaptation if the system later moves to Temporal.

## Revisit Triggers

Revisit this decision if:

- sustained concurrent workflows exceed 50 per minute
- workflow state loss is observed
- cross-service orchestration becomes required
- Redis checkpointing proves insufficient
- failure recovery becomes difficult to reason about

