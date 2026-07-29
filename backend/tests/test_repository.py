from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, ReviewRepository, create_async_sessionmaker, create_engine
from app.models import (
    AgentType,
    Evidence,
    Finding,
    FindingSeverity,
    HitlStatus,
    PullRequestRef,
    RepositoryRef,
    ReviewStatus,
    WebhookEvent,
)


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
async def test_repository_creates_review_and_findings(session: AsyncSession) -> None:
    repo = ReviewRepository(session)
    review = await repo.create_review(
        repo_full_name="acme/shop",
        pull_request_number=7,
        head_sha="abcdef123",
        base_sha="123456789",
        status=ReviewStatus.RUNNING,
    )
    finding = Finding(
        review_id=review.id,
        agent_type=AgentType.SECURITY,
        severity=FindingSeverity.HIGH,
        category="sql-injection",
        summary="Unsafe SQL query uses request input.",
        file_path="backend/app/search.py",
        line_start=42,
        confidence=0.9,
        rationale="The query interpolates user input.",
        evidence=[Evidence(source="retrieval", path="backend/app/search.py", rank=1)],
    )

    records = await repo.save_findings([finding])
    await session.commit()

    assert len(records) == 1
    saved_findings = await repo.list_findings(review.id)
    assert saved_findings[0].summary == "Unsafe SQL query uses request input."
    assert saved_findings[0].evidence[0]["source"] == "retrieval"


@pytest.mark.asyncio
async def test_repository_updates_review_status(session: AsyncSession) -> None:
    repo = ReviewRepository(session)
    review = await repo.create_review(
        repo_full_name="acme/shop",
        pull_request_number=7,
        head_sha="abcdef123",
    )

    updated = await repo.update_review_status(
        review.id,
        ReviewStatus.AWAITING_HUMAN,
        overall_confidence=0.51,
        routing_reason="below confidence threshold",
    )

    assert updated.status == "awaiting_human"
    assert updated.overall_confidence == 0.51
    assert updated.routing_reason == "below confidence threshold"


@pytest.mark.asyncio
async def test_repository_records_hitl_decision_and_feedback(
    session: AsyncSession,
) -> None:
    repo = ReviewRepository(session)
    review = await repo.create_review(
        repo_full_name="acme/shop",
        pull_request_number=7,
        head_sha="abcdef123",
    )
    hitl = await repo.create_hitl_review(
        review_id=review.id,
        reason="critical finding requires approval",
    )

    decided = await repo.record_hitl_decision(
        hitl.id,
        status=HitlStatus.APPROVED,
        decided_by="senior@example.com",
        decision_note="Valid finding.",
    )
    feedback = await repo.record_feedback(
        review_id=review.id,
        feedback_type="accepted",
        note="Good catch.",
        created_by="senior@example.com",
    )

    assert decided.status == "approved"
    assert decided.decided_by == "senior@example.com"
    assert feedback.feedback_type == "accepted"


@pytest.mark.asyncio
async def test_repository_records_webhook_and_idempotency(
    session: AsyncSession,
) -> None:
    repo = ReviewRepository(session)
    event = WebhookEvent(
        delivery_id="delivery-1",
        event_name="pull_request",
        action="opened",
        repository=RepositoryRef(id=1, full_name="acme/shop", default_branch="main"),
        pull_request=PullRequestRef(
            id=2,
            number=7,
            title="Add checkout",
            head_sha="abcdef123",
            base_sha="123456789",
        ),
    )

    delivery = await repo.record_webhook_delivery(event, payload={"action": "opened"})
    assert delivery.delivery_id == "delivery-1"

    key = str(uuid4())
    assert not await repo.has_idempotency_key(key, scope="github-webhook")
    await repo.create_idempotency_key(key, scope="github-webhook", result_ref="review-1")
    assert await repo.has_idempotency_key(key, scope="github-webhook")
