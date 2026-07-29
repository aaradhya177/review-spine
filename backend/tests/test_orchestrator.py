import pytest

from app.core.workflow_engine import WorkflowInput
from app.orchestrator import LangGraphWorkflowEngine
from app.orchestrator.nodes import SPECIALIST_NODES


def make_input() -> WorkflowInput:
    return WorkflowInput(
        delivery_id="delivery-1",
        repo_full_name="acme/shop",
        pull_request_number=7,
        head_sha="abcdef123",
        base_sha="123456789",
        webhook_event_id="event-1",
    )


@pytest.mark.asyncio
async def test_langgraph_engine_runs_local_graph_end_to_end() -> None:
    engine = LangGraphWorkflowEngine(use_langgraph=False)

    state = await engine.run("review:delivery-1", make_input())

    assert state.status == "completed"
    assert state.current_node == "route_result"
    assert state.completed_nodes[0] == "build_context"
    assert state.completed_nodes[-1] == "route_result"


@pytest.mark.asyncio
async def test_all_specialists_complete_before_aggregate() -> None:
    engine = LangGraphWorkflowEngine(use_langgraph=False)

    state = await engine.run("review:delivery-1", make_input())

    aggregate_index = state.completed_nodes.index("aggregate")
    for node in SPECIALIST_NODES:
        assert state.completed_nodes.index(node) < aggregate_index


@pytest.mark.asyncio
async def test_langgraph_engine_state_is_serializable() -> None:
    engine = LangGraphWorkflowEngine(use_langgraph=False)

    state = await engine.run("review:delivery-1", make_input())

    dumped = state.model_dump(mode="json")
    assert dumped["input"]["repo_full_name"] == "acme/shop"
    assert dumped["findings"] == []

