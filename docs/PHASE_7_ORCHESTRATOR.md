# Phase 7: LangGraph Orchestrator

Phase 7 adds the orchestrator module behind the `WorkflowEngine` interface.

## Modules

- `backend/app/orchestrator/state.py`
- `backend/app/orchestrator/nodes.py`
- `backend/app/orchestrator/graph.py`
- `backend/app/orchestrator/langgraph_engine.py`

## Current Graph

The graph nodes are:

- `build_context`
- `security_agent`
- `quality_agent`
- `tests_agent`
- `docs_agent`
- `aggregate`
- `route_result`

The specialist nodes currently return empty finding lists. Later phases will replace those stubs with real retrieval and LLM-backed agents.

## LangGraph Dependency

`LangGraphWorkflowEngine` uses LangGraph when installed. Tests use the deterministic local graph path so the project remains runnable without provider or Redis credentials.

The dependency boundary from ADR-001 still holds: outer modules use `app.core.workflow_engine`; LangGraph-specific imports stay inside `backend/app/orchestrator`.

