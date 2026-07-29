from uuid import uuid4

import pytest

from app.agents import (
    AgentInput,
    DocsReviewAgent,
    QualityReviewAgent,
    SecurityReviewAgent,
    TestsReviewAgent,
)
from app.config import Settings
from app.economics import BudgetGuard, InMemoryCostRepository
from app.memory.context_retriever import RetrievedContext
from app.models.enums import AgentType
from app.prompts import PromptRegistry
from app.tools import FakeLLMProvider, LLMClient, LLMResponse, ModelRouter


class FakeRetriever:
    async def retrieve(self, **kwargs):
        return [
            RetrievedContext(
                path="app.py",
                symbol=None,
                content="def changed(): pass",
                rank=1,
                score=0.5,
                method="keyword",
            )
        ]


def make_input() -> AgentInput:
    return AgentInput(
        review_id=uuid4(),
        repo_full_name="acme/shop",
        pull_request_number=7,
        diff_text="diff text",
        changed_files=["app.py"],
    )


def make_agent(agent_cls, response: LLMResponse):
    client = LLMClient(
        FakeLLMProvider(response),
        budget_guard=BudgetGuard(
            InMemoryCostRepository(daily_cost_usd=0.0),
            daily_limit_usd=10.0,
        ),
    )
    return agent_cls(
        retriever=FakeRetriever(),  # type: ignore[arg-type]
        prompt_registry=PromptRegistry(),
        llm_client=client,
        model_router=ModelRouter(Settings(default_review_model="review-model")),
        timeout_seconds=1,
    )


@pytest.mark.parametrize(
    ("agent_cls", "agent_type", "category"),
    [
        (SecurityReviewAgent, AgentType.SECURITY, "auth-bypass"),
        (QualityReviewAgent, AgentType.QUALITY, "edge-case"),
        (TestsReviewAgent, AgentType.TESTS, "missing-test"),
        (DocsReviewAgent, AgentType.DOCS, "missing-docs"),
    ],
)
@pytest.mark.asyncio
async def test_specialist_agent_maps_structured_response_to_finding(
    agent_cls,
    agent_type: AgentType,
    category: str,
) -> None:
    agent = make_agent(
        agent_cls,
        LLMResponse(
            content={
                "findings": [
                    {
                        "severity": "MEDIUM",
                        "category": category,
                        "summary": "Useful finding.",
                        "file_path": "app.py",
                        "line_start": 3,
                        "confidence": 0.7,
                        "rationale": "The evidence supports this finding.",
                    }
                ]
            },
            tokens_in=1,
            tokens_out=1,
            cost_usd=0.0,
        ),
    )

    result = await agent.run(make_input())

    assert result.agent_type == agent_type.value
    assert len(result.findings) == 1
    assert result.findings[0].agent_type == agent_type
    assert result.findings[0].category == category


@pytest.mark.asyncio
async def test_security_agent_filters_info_findings() -> None:
    agent = make_agent(
        SecurityReviewAgent,
        LLMResponse(
            content={
                "findings": [
                    {
                        "severity": "INFO",
                        "category": "style",
                        "summary": "Low value security note.",
                        "file_path": "app.py",
                        "line_start": 3,
                        "confidence": 0.9,
                        "rationale": "Informational only.",
                    }
                ]
            },
            tokens_in=1,
            tokens_out=1,
            cost_usd=0.0,
        ),
    )

    result = await agent.run(make_input())

    assert result.findings == []

