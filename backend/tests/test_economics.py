from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import Base, create_async_sessionmaker, create_engine
from app.economics import AgentCostSummary, BudgetExceededError, BudgetGuard, CostRepository
from app.api.economics_router import InMemoryEconomicsService
from app.main import create_app
from app.observability.events import AgentEvent, emit_agent_event


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
async def test_cost_repository_summarizes_agent_cost(session: AsyncSession) -> None:
    review_id = uuid4()
    await emit_agent_event(session, AgentEvent(review_id=review_id, agent="security", event_type="llm.call", cost_usd=0.01, tokens_in=10, tokens_out=5, latency_ms=100))
    await emit_agent_event(session, AgentEvent(review_id=review_id, agent="security", event_type="llm.call", cost_usd=0.02, tokens_in=20, tokens_out=10, latency_ms=200))
    await session.commit()
    repo = CostRepository(session)

    summaries = await repo.cost_by_agent()

    assert summaries[0].agent == "security"
    assert summaries[0].cost_usd == 0.03
    assert summaries[0].tokens_in == 30
    assert await repo.pr_cost(review_id) == 0.03


@pytest.mark.asyncio
async def test_budget_guard_blocks_from_event_cost(session: AsyncSession) -> None:
    await emit_agent_event(session, AgentEvent(review_id=uuid4(), agent="quality", event_type="llm.call", cost_usd=1.0))
    await session.commit()
    guard = BudgetGuard(CostRepository(session), daily_limit_usd=1.0)

    with pytest.raises(BudgetExceededError):
        await guard.check()


def test_economics_api_returns_summaries() -> None:
    app = create_app(Settings(app_env="test"))
    app.state.economics_service = InMemoryEconomicsService(
        [AgentCostSummary(agent="security", llm_calls=1, cost_usd=0.1, tokens_in=10, tokens_out=5)],
        daily_cost=0.1,
    )
    client = TestClient(app)

    response = client.get("/economics/agents")

    assert response.status_code == 200
    assert response.json()[0]["agent"] == "security"

