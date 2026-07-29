# Phase 8: Event Spine

Phase 8 introduces the durable event shape used for traces, audit, and cost attribution.

## Table

`agent_events` records:

- timestamp
- review id
- agent
- span id and parent span
- event type
- model
- token counts
- cost
- latency
- outcome
- confidence
- JSON payload

The migration creates a normal table and indexes locally. If TimescaleDB is present, it converts the table to a hypertable partitioned by `ts`.

## Code

`backend/app/observability/events.py` provides:

- `AgentEvent`
- `emit_agent_event`
- `get_review_trace`

Later phases will wire these calls into every workflow node and LLM/tool call.

