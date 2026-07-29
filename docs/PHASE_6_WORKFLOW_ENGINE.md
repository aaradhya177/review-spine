# Phase 6: Workflow Engine Interface

The queue worker calls a shared workflow abstraction instead of importing orchestration implementation details.

## Contract

`backend/app/core/workflow_engine.py` defines:

- `WorkflowInput`
- `WorkflowState`
- `WorkflowEngine`
- `StubWorkflowEngine`

The required interface is:

- `run(workflow_id, input)`
- `resume(workflow_id, state)`
- `get_state(workflow_id)`

## Current Implementation

`StubWorkflowEngine` is deterministic and serializable. It marks the expected future nodes as completed:

- `build_context`
- `security_agent`
- `quality_agent`
- `tests_agent`
- `docs_agent`
- `aggregate`
- `route_result`

Phase 7 will add a LangGraph implementation behind this same interface.

## Boundary Rule

Outside `backend/app/orchestrator`, code should import from `app.core.workflow_engine`, not LangGraph.

