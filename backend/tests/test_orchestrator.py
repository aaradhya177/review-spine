from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, create_async_sessionmaker, create_engine
from app.core.workflow_engine import WorkflowInput
from app.observability.events import get_review_trace
from app.orchestrator import LangGraphWorkflowEngine
from app.orchestrator.nodes import SPECIALIST_NODES


def make_input() -> WorkflowInput:
    return WorkflowInput(
        delivery_id="delivery-1",
        repo_full_name="acme/shop",
        pull_request_number=7,
        head_sha="abcdef123",
        base_sha="123456789",
        webhook_event_id=str(uuid4()),
    )


@pytest_asyncio.fixture
async def session():
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = create_async_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session

    await engine.dispose()


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


@pytest.mark.asyncio
async def test_orchestrator_emits_span_events(session: AsyncSession) -> None:
    engine = LangGraphWorkflowEngine(use_langgraph=False, event_session=session)

    state = await engine.run("review:delivery-1", make_input())
    await session.commit()

    trace = await get_review_trace(session, review_id=state.input.webhook_event_id)
    assert [event.event_type for event in trace] == ["span.start", "span.end"]
    assert trace[-1].outcome == "completed"
