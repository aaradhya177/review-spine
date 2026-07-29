from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentResult, AggregationPolicy, ReviewAggregator
from app.database import (
    Base,
    HitlReviewRecord,
    ReviewRepository,
    create_async_sessionmaker,
    create_engine,
)
from app.models.enums import AgentType, FindingSeverity, ReviewStatus
from app.models.findings import Finding


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = create_async_sessionmaker(engine)
    async with sessionmaker() as session:
        yield session

    await engine.dispose()


def finding(
    *,
    review_id: UUID,
    agent_type: AgentType = AgentType.QUALITY,
    severity: FindingSeverity = FindingSeverity.MEDIUM,
    confidence: float = 0.9,
    category: str = "edge-case",
    line_start: int = 10,
) -> Finding:
    return Finding(
        review_id=review_id,
        agent_type=agent_type,
        severity=severity,
        category=category,
        summary="Useful finding.",
        file_path="app.py",
        line_start=line_start,
        confidence=confidence,
        rationale="Evidence supports this.",
    )


@pytest.mark.asyncio
async def test_aggregator_deduplicates_by_location_and_category() -> None:
    review_id = uuid4()
    lower = finding(review_id=review_id, confidence=0.5)
    higher = finding(review_id=review_id, confidence=0.9)
    aggregator = ReviewAggregator()

    decision = await aggregator.aggregate(
        review_id=review_id,
        agent_results=[
            AgentResult(agent_type="quality", findings=[lower]),
            AgentResult(agent_type="tests", findings=[higher]),
        ],
    )

    assert decision.findings == [higher]
    assert decision.overall_confidence == 0.9


@pytest.mark.asyncio
async def test_aggregator_routes_critical_to_escalation(session: AsyncSession) -> None:
    repo = ReviewRepository(session)
    review = await repo.create_review(
        repo_full_name="acme/shop",
        pull_request_number=7,
        head_sha="abcdef123",
    )
    aggregator = ReviewAggregator(repository=repo)

    decision = await aggregator.aggregate(
        review_id=UUID(review.id),
        agent_results=[
            AgentResult(
                agent_type="security",
                findings=[
                    finding(
                        review_id=UUID(review.id),
                        agent_type=AgentType.SECURITY,
                        severity=FindingSeverity.CRITICAL,
                        category="auth-bypass",
                    )
                ],
            )
        ],
    )
    await session.commit()
    saved = await repo.get_review(review.id)
    hitl = await session.execute(select(HitlReviewRecord))

    assert decision.route == "escalate"
    assert saved is not None
    assert saved.status == ReviewStatus.ESCALATED.value
    assert hitl.scalar_one().reason == "critical finding requires human escalation"


@pytest.mark.asyncio
async def test_aggregator_routes_low_confidence_to_human_review() -> None:
    review_id = uuid4()
    aggregator = ReviewAggregator(
        policy=AggregationPolicy(auto_post_confidence_threshold=0.82)
    )

    decision = await aggregator.aggregate(
        review_id=review_id,
        agent_results=[
            AgentResult(
                agent_type="quality",
                findings=[finding(review_id=review_id, confidence=0.5)],
            )
        ],
    )

    assert decision.route == "human_review"
    assert decision.reason == "overall confidence below auto-post threshold"


@pytest.mark.asyncio
async def test_aggregator_auto_posts_confident_noncritical_findings() -> None:
    review_id = uuid4()
    aggregator = ReviewAggregator(
        policy=AggregationPolicy(auto_post_confidence_threshold=0.82)
    )

    decision = await aggregator.aggregate(
        review_id=review_id,
        agent_results=[
            AgentResult(
                agent_type="quality",
                findings=[finding(review_id=review_id, confidence=0.95)],
            )
        ],
    )

    assert decision.route == "auto_post"
    assert decision.overall_confidence == 0.95

