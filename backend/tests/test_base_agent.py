from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentInput, BaseReviewAgent
from app.config import Settings
from app.database import Base, create_async_sessionmaker, create_engine
from app.economics import BudgetGuard, InMemoryCostRepository
from app.memory.context_retriever import RetrievedContext
from app.models.enums import AgentType
from app.observability.events import get_review_trace
from app.prompts import PromptRegistry
from app.tools import FakeLLMProvider, LLMClient, LLMResponse, ModelRouter


class FakeRetriever:
    def __init__(self) -> None:
        self.calls = []

    async def retrieve(self, **kwargs):
        self.calls.append(kwargs)
        return [
            RetrievedContext(
                path="billing/stripe.py",
                symbol=None,
                content="def charge_customer(customer_id): pass",
                rank=1,
                score=0.5,
                method="keyword",
            )
        ]


class SecurityTestAgent(BaseReviewAgent):
    agent_type = AgentType.SECURITY
    prompt_name = "security"

    def concern(self) -> str:
        return "security"


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = create_async_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session

    await engine.dispose()


def make_input() -> AgentInput:
    return AgentInput(
        review_id=uuid4(),
        repo_full_name="acme/shop",
        pull_request_number=7,
        diff_text="diff --git a/billing/stripe.py b/billing/stripe.py",
        changed_files=["billing/stripe.py"],
    )


def make_agent(provider: FakeLLMProvider, session: AsyncSession | None = None):
    retriever = FakeRetriever()
    client = LLMClient(
        provider,
        budget_guard=BudgetGuard(
            InMemoryCostRepository(daily_cost_usd=0.0),
            daily_limit_usd=10.0,
        ),
        event_session=session,
    )
    agent = SecurityTestAgent(
        retriever=retriever,  # type: ignore[arg-type]
        prompt_registry=PromptRegistry(),
        llm_client=client,
        model_router=ModelRouter(Settings(default_review_model="review-model")),
        event_session=session,
        timeout_seconds=1,
        max_attempts=1,
    )
    return agent, retriever


@pytest.mark.asyncio
async def test_base_agent_runs_retrieval_prompt_llm_and_validation(
    session: AsyncSession,
) -> None:
    provider = FakeLLMProvider(
        LLMResponse(
            content={
                "confidence": 0.8,
                "findings": [
                    {
                        "severity": "HIGH",
                        "category": "sql-injection",
                        "summary": "Unsafe SQL query.",
                        "file_path": "billing/stripe.py",
                        "line_start": 10,
                        "suggestion": "Use bind parameters.",
                        "confidence": 0.8,
                        "rationale": "User input reaches SQL.",
                    }
                ],
            },
            tokens_in=10,
            tokens_out=20,
            cost_usd=0.01,
        )
    )
    agent, retriever = make_agent(provider, session=session)
    input = make_input()

    result = await agent.run(input)
    await session.commit()

    assert result.agent_type == "security"
    assert result.confidence == 0.8
    assert len(result.findings) == 1
    assert result.findings[0].evidence[0].path == "billing/stripe.py"
    assert retriever.calls[0]["agent_type"] == "security"
    assert "billing/stripe.py" in provider.requests[0].prompt
    trace = await get_review_trace(session, review_id=input.review_id)
    assert [event.event_type for event in trace] == [
        "span.start",
        "llm.call",
        "span.end",
    ]


@pytest.mark.asyncio
async def test_base_agent_handles_invalid_llm_output() -> None:
    provider = FakeLLMProvider(
        LLMResponse(
            content={"findings": [{"severity": "HIGH"}]},
            tokens_in=1,
            tokens_out=1,
            cost_usd=0.0,
        )
    )
    agent, _retriever = make_agent(provider)

    result = await agent.run(make_input())

    assert result.findings == []
    assert result.errors
    assert result.metadata["raw_finding_count"] == 1


@pytest.mark.asyncio
async def test_base_agent_returns_error_result_when_provider_fails() -> None:
    class FailingProvider:
        async def complete_structured(self, request):
            raise RuntimeError("provider down")

    client = LLMClient(
        FailingProvider(),
        budget_guard=BudgetGuard(
            InMemoryCostRepository(daily_cost_usd=0.0),
            daily_limit_usd=10.0,
        ),
    )
    agent = SecurityTestAgent(
        retriever=FakeRetriever(),  # type: ignore[arg-type]
        prompt_registry=PromptRegistry(),
        llm_client=client,
        model_router=ModelRouter(Settings(default_review_model="review-model")),
        timeout_seconds=1,
        max_attempts=1,
    )

    result = await agent.run(make_input())

    assert result.confidence == 0.0
    assert result.errors == ["provider down"]

