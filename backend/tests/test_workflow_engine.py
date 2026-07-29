from uuid import uuid4

import pytest

from app.core import StubWorkflowEngine, WorkflowInput, WorkflowState


def make_input() -> WorkflowInput:
    return WorkflowInput(
        delivery_id="delivery-1",
        repo_full_name="acme/shop",
        pull_request_number=7,
        head_sha="abcdef123",
        base_sha="123456789",
        webhook_event_id=str(uuid4()),
    )


@pytest.mark.asyncio
async def test_stub_workflow_engine_run_is_serializable() -> None:
    engine = StubWorkflowEngine()

    state = await engine.run("review:delivery-1", make_input())

    assert state.status == "completed"
    assert state.completed_nodes[-1] == "route_result"
    assert state.model_dump(mode="json")["input"]["repo_full_name"] == "acme/shop"


@pytest.mark.asyncio
async def test_stub_workflow_engine_resume_updates_state() -> None:
    engine = StubWorkflowEngine()
    state = WorkflowState(
        workflow_id="old",
        status="paused",
        input=make_input(),
        completed_nodes=["build_context"],
    )

    resumed = await engine.resume("review:delivery-1", state)

    assert resumed.workflow_id == "review:delivery-1"
    assert resumed.status == "completed"
    assert await engine.get_state("review:delivery-1") == resumed
