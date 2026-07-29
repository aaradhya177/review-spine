from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import Base, create_async_sessionmaker, create_engine
from app.economics import BudgetExceededError, BudgetGuard, InMemoryCostRepository
from app.models.enums import AgentType
from app.observability.events import get_review_trace
from app.prompts import PromptRegistry
from app.tools import FakeLLMProvider, LLMClient, LLMRequest, LLMResponse, ModelRouter


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = create_async_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session

    await engine.dispose()


def test_prompt_registry_loads_and_renders_versioned_template() -> None:
    registry = PromptRegistry()

    prompt = registry.get("security", "v1")
    rendered = prompt.render(diff="diff text", context="context text")

    assert prompt.prompt_id == "security@v1"
    assert "diff text" in rendered
    assert "context text" in rendered


def test_model_router_uses_default_model_when_configured() -> None:
    router = ModelRouter(Settings(default_review_model="gpt-review"))

    assert router.choose_review_model(AgentType.SECURITY) == "gpt-review"


@pytest.mark.asyncio
async def test_budget_guard_blocks_when_daily_limit_reached() -> None:
    guard = BudgetGuard(InMemoryCostRepository(daily_cost_usd=3.0), daily_limit_usd=3.0)

    with pytest.raises(BudgetExceededError):
        await guard.check()


@pytest.mark.asyncio
async def test_llm_client_records_event_after_structured_call(
    session: AsyncSession,
) -> None:
    review_id = uuid4()
    provider = FakeLLMProvider(
        LLMResponse(
            content={"findings": []},
            tokens_in=10,
            tokens_out=5,
            cost_usd=0.003,
        )
    )
    client = LLMClient(
        provider,
        budget_guard=BudgetGuard(
            InMemoryCostRepository(daily_cost_usd=0.0),
            daily_limit_usd=1.0,
        ),
        event_session=session,
    )

    response = await client.complete_structured(
        LLMRequest(
            review_id=review_id,
            agent="security",
            model="review-model",
            prompt="review this",
            prompt_version="security@v1",
            response_schema="FindingList",
        )
    )
    await session.commit()

    assert response.content == {"findings": []}
    assert provider.requests[0].prompt_version == "security@v1"
    trace = await get_review_trace(session, review_id=review_id)
    assert trace[0].event_type == "llm.call"
    assert trace[0].payload["prompt_version"] == "security@v1"

