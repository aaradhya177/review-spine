from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AgentEventRecord


class AgentEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    review_id: UUID
    agent: str = Field(min_length=1)
    span_id: UUID = Field(default_factory=uuid4)
    parent_span: UUID | None = None
    event_type: str = Field(min_length=1)
    model: str | None = None
    tokens_in: int | None = Field(default=None, ge=0)
    tokens_out: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0.0)
    latency_ms: int | None = Field(default=None, ge=0)
    outcome: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    payload: dict = Field(default_factory=dict)


def event_to_record(event: AgentEvent) -> AgentEventRecord:
    return AgentEventRecord(
        id=str(event.id),
        ts=event.ts,
        review_id=str(event.review_id),
        agent=event.agent,
        span_id=str(event.span_id),
        parent_span=str(event.parent_span) if event.parent_span else None,
        event_type=event.event_type,
        model=event.model,
        tokens_in=event.tokens_in,
        tokens_out=event.tokens_out,
        cost_usd=event.cost_usd,
        latency_ms=event.latency_ms,
        outcome=event.outcome,
        confidence=event.confidence,
        payload=event.payload,
    )


async def emit_agent_event(session: AsyncSession, event: AgentEvent) -> AgentEventRecord:
    record = event_to_record(event)
    session.add(record)
    await session.flush()
    return record


async def get_review_trace(
    session: AsyncSession,
    *,
    review_id: UUID | str,
) -> list[AgentEventRecord]:
    result = await session.execute(
        select(AgentEventRecord)
        .where(AgentEventRecord.review_id == str(review_id))
        .order_by(AgentEventRecord.ts, AgentEventRecord.id)
    )
    return list(result.scalars())

