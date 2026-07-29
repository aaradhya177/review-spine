from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, create_async_sessionmaker, create_engine
from app.observability.events import AgentEvent, emit_agent_event, get_review_trace


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = create_async_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_emit_agent_event_persists_cost_and_payload(session: AsyncSession) -> None:
    review_id = uuid4()

    record = await emit_agent_event(
        session,
        AgentEvent(
            review_id=review_id,
            agent="security",
            event_type="llm.call",
            model="review-model",
            tokens_in=100,
            tokens_out=20,
            cost_usd=0.012,
            latency_ms=850,
            confidence=0.9,
            payload={"prompt_version": "security@1"},
        ),
    )
    await session.commit()

    assert record.review_id == str(review_id)
    assert record.payload["prompt_version"] == "security@1"
    assert float(record.cost_usd) == 0.012


@pytest.mark.asyncio
async def test_get_review_trace_orders_events_by_time(session: AsyncSession) -> None:
    review_id = uuid4()
    first = AgentEvent(review_id=review_id, agent="worker", event_type="span.start")
    second = AgentEvent(review_id=review_id, agent="worker", event_type="span.end")
    await emit_agent_event(session, second)
    await emit_agent_event(session, first)
    await session.commit()

    trace = await get_review_trace(session, review_id=review_id)

    assert [event.event_type for event in trace] == ["span.start", "span.end"]

