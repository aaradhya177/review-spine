from time import perf_counter
from typing import Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.economics.budget import BudgetGuard
from app.observability.events import AgentEvent, emit_agent_event


class LLMRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: UUID
    agent: str = Field(min_length=1)
    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    response_schema: str | None = None


class LLMResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: dict[str, Any]
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    cost_usd: float = Field(ge=0.0)


class LLMProvider(Protocol):
    async def complete_structured(self, request: LLMRequest) -> LLMResponse:
        """Return structured LLM output."""


class FakeLLMProvider:
    def __init__(self, response: LLMResponse | None = None):
        self.response = response or LLMResponse(
            content={"findings": []},
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
        )
        self.requests: list[LLMRequest] = []

    async def complete_structured(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return self.response


class LLMClient:
    def __init__(
        self,
        provider: LLMProvider,
        *,
        budget_guard: BudgetGuard,
        event_session: AsyncSession | None = None,
    ):
        self.provider = provider
        self.budget_guard = budget_guard
        self.event_session = event_session

    async def complete_structured(self, request: LLMRequest) -> LLMResponse:
        await self.budget_guard.check()
        start = perf_counter()
        response = await self.provider.complete_structured(request)
        latency_ms = int((perf_counter() - start) * 1000)
        if self.event_session is not None:
            await emit_agent_event(
                self.event_session,
                AgentEvent(
                    review_id=request.review_id,
                    agent=request.agent,
                    event_type="llm.call",
                    model=request.model,
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    cost_usd=response.cost_usd,
                    latency_ms=latency_ms,
                    payload={
                        "prompt_version": request.prompt_version,
                        "response_schema": request.response_schema,
                    },
                ),
            )
        return response

