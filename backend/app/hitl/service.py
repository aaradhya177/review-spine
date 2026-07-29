from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import HitlStatus


class HitlReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    review_id: UUID
    status: HitlStatus
    reason: str
    assigned_to: str | None = None


class HitlDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decided_by: str = Field(min_length=1)
    note: str | None = None


class HitlDisputeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created_by: str = Field(min_length=1)
    note: str = Field(min_length=1)


class HitlService(Protocol):
    async def list_pending(self) -> list[HitlReviewItem]:
        """List pending HITL review items."""

    async def get(self, hitl_id: UUID) -> HitlReviewItem:
        """Get one HITL review item."""

    async def decide(
        self,
        hitl_id: UUID,
        *,
        status: HitlStatus,
        decided_by: str,
        note: str | None = None,
    ) -> HitlReviewItem:
        """Approve, reject, or escalate an item."""

    async def dispute(
        self,
        review_id: UUID,
        *,
        created_by: str,
        note: str,
    ) -> HitlReviewItem:
        """Record a developer dispute and return the created HITL item."""


class InMemoryHitlService:
    def __init__(self, items: list[HitlReviewItem] | None = None):
        self.items: dict[UUID, HitlReviewItem] = {
            item.id: item for item in (items or [])
        }
        self.decisions: list[dict] = []
        self.disputes: list[dict] = []

    async def list_pending(self) -> list[HitlReviewItem]:
        return [
            item
            for item in self.items.values()
            if item.status == HitlStatus.PENDING
        ]

    async def get(self, hitl_id: UUID) -> HitlReviewItem:
        if hitl_id not in self.items:
            raise LookupError(f"HITL item not found: {hitl_id}")
        return self.items[hitl_id]

    async def decide(
        self,
        hitl_id: UUID,
        *,
        status: HitlStatus,
        decided_by: str,
        note: str | None = None,
    ) -> HitlReviewItem:
        item = await self.get(hitl_id)
        updated = item.model_copy(update={"status": status})
        self.items[hitl_id] = updated
        self.decisions.append(
            {
                "hitl_id": hitl_id,
                "status": status.value,
                "decided_by": decided_by,
                "note": note,
            }
        )
        return updated

    async def dispute(
        self,
        review_id: UUID,
        *,
        created_by: str,
        note: str,
    ) -> HitlReviewItem:
        item = HitlReviewItem(
            id=uuid4(),
            review_id=review_id,
            status=HitlStatus.DISPUTED,
            reason=note,
        )
        self.items[item.id] = item
        self.disputes.append(
            {"review_id": review_id, "created_by": created_by, "note": note}
        )
        return item

