from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AgentEventRecord


class AgentCostSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent: str
    llm_calls: int = Field(ge=0)
    cost_usd: float = Field(ge=0.0)
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    p95_latency_ms: int | None = None


class CostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_daily_cost_usd(self) -> float:
        since = datetime.now(UTC) - timedelta(days=1)
        result = await self.session.execute(
            select(AgentEventRecord).where(
                AgentEventRecord.event_type == "llm.call",
                AgentEventRecord.ts >= since,
            )
        )
        return round(
            sum(float(event.cost_usd or 0.0) for event in result.scalars()),
            6,
        )

    async def cost_by_agent(self) -> list[AgentCostSummary]:
        result = await self.session.execute(
            select(AgentEventRecord).where(AgentEventRecord.event_type == "llm.call")
        )
        grouped: dict[str, list[AgentEventRecord]] = {}
        for event in result.scalars():
            grouped.setdefault(event.agent, []).append(event)

        return [
            AgentCostSummary(
                agent=agent,
                llm_calls=len(events),
                cost_usd=round(sum(float(event.cost_usd or 0.0) for event in events), 6),
                tokens_in=sum(event.tokens_in or 0 for event in events),
                tokens_out=sum(event.tokens_out or 0 for event in events),
                p95_latency_ms=p95([event.latency_ms for event in events if event.latency_ms is not None]),
            )
            for agent, events in sorted(grouped.items())
        ]

    async def pr_cost(self, review_id: UUID | str) -> float:
        result = await self.session.execute(
            select(AgentEventRecord).where(
                AgentEventRecord.review_id == str(review_id),
                AgentEventRecord.event_type == "llm.call",
            )
        )
        return round(sum(float(event.cost_usd or 0.0) for event in result.scalars()), 6)


def p95(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))
    return ordered[index]

