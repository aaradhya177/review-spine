from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    FindingRecord,
    HitlFeedbackRecord,
    HitlReviewRecord,
    IdempotencyRecord,
    PrReviewRecord,
    WebhookDeliveryRecord,
    now_utc,
)
from app.models.enums import HitlStatus, ReviewStatus
from app.models.findings import Finding
from app.models.webhook import WebhookEvent


class ReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_review(
        self,
        *,
        repo_full_name: str,
        pull_request_number: int,
        head_sha: str,
        base_sha: str | None = None,
        status: ReviewStatus = ReviewStatus.QUEUED,
    ) -> PrReviewRecord:
        review = PrReviewRecord(
            repo_full_name=repo_full_name,
            pull_request_number=pull_request_number,
            head_sha=head_sha,
            base_sha=base_sha,
            status=status.value,
        )
        self.session.add(review)
        await self.session.flush()
        return review

    async def get_review(self, review_id: UUID | str) -> PrReviewRecord | None:
        return await self.session.get(PrReviewRecord, str(review_id))

    async def update_review_status(
        self,
        review_id: UUID | str,
        status: ReviewStatus,
        *,
        overall_confidence: float | None = None,
        routing_reason: str | None = None,
        github_review_id: str | None = None,
    ) -> PrReviewRecord:
        review = await self.session.get(PrReviewRecord, str(review_id))
        if review is None:
            raise LookupError(f"Review not found: {review_id}")
        review.status = status.value
        review.updated_at = now_utc()
        if overall_confidence is not None:
            review.overall_confidence = overall_confidence
        if routing_reason is not None:
            review.routing_reason = routing_reason
        if github_review_id is not None:
            review.github_review_id = github_review_id
        await self.session.flush()
        return review

    async def save_findings(self, findings: list[Finding]) -> list[FindingRecord]:
        records = [FindingRecord.from_domain(finding) for finding in findings]
        self.session.add_all(records)
        await self.session.flush()
        return records

    async def list_findings(self, review_id: UUID | str) -> list[FindingRecord]:
        result = await self.session.execute(
            select(FindingRecord)
            .where(FindingRecord.review_id == str(review_id))
            .order_by(FindingRecord.severity, FindingRecord.file_path, FindingRecord.line_start)
        )
        return list(result.scalars())

    async def create_hitl_review(
        self,
        *,
        review_id: UUID | str,
        reason: str,
        assigned_to: str | None = None,
    ) -> HitlReviewRecord:
        record = HitlReviewRecord(
            review_id=str(review_id),
            reason=reason,
            assigned_to=assigned_to,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def record_hitl_decision(
        self,
        hitl_id: UUID | str,
        *,
        status: HitlStatus,
        decided_by: str,
        decision_note: str | None = None,
    ) -> HitlReviewRecord:
        hitl = await self.session.get(HitlReviewRecord, str(hitl_id))
        if hitl is None:
            raise LookupError(f"HITL review not found: {hitl_id}")
        hitl.status = status.value
        hitl.decided_by = decided_by
        hitl.decision_note = decision_note
        hitl.decided_at = now_utc()
        await self.session.flush()
        return hitl

    async def record_feedback(
        self,
        *,
        review_id: UUID | str,
        feedback_type: str,
        finding_id: UUID | str | None = None,
        note: str | None = None,
        created_by: str | None = None,
    ) -> HitlFeedbackRecord:
        feedback = HitlFeedbackRecord(
            review_id=str(review_id),
            finding_id=str(finding_id) if finding_id else None,
            feedback_type=feedback_type,
            note=note,
            created_by=created_by,
        )
        self.session.add(feedback)
        await self.session.flush()
        return feedback

    async def record_webhook_delivery(
        self,
        event: WebhookEvent,
        *,
        payload: dict,
        status: str = "received",
    ) -> WebhookDeliveryRecord:
        record = WebhookDeliveryRecord(
            delivery_id=event.delivery_id,
            event_name=event.event_name,
            action=event.action,
            repo_full_name=event.repository.full_name,
            pull_request_number=event.pull_request.number,
            payload=payload,
            status=status,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def has_idempotency_key(self, key: str, *, scope: str) -> bool:
        existing = await self.session.get(IdempotencyRecord, key)
        return existing is not None and existing.scope == scope

    async def create_idempotency_key(
        self,
        key: str,
        *,
        scope: str,
        result_ref: str | None = None,
    ) -> IdempotencyRecord:
        record = IdempotencyRecord(key=key, scope=scope, result_ref=result_ref)
        self.session.add(record)
        await self.session.flush()
        return record

