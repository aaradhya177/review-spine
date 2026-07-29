from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.hitl.service import (
    HitlDecisionRequest,
    HitlDisputeRequest,
    HitlReviewItem,
    HitlService,
    InMemoryHitlService,
)
from app.models.enums import HitlStatus

router = APIRouter(prefix="/hitl", tags=["hitl"])

_fallback_service = InMemoryHitlService()


def get_hitl_service(request: Request) -> HitlService:
    return getattr(request.app.state, "hitl_service", _fallback_service)


@router.get("/reviews", response_model=list[HitlReviewItem])
async def list_pending_reviews(
    service: Annotated[HitlService, Depends(get_hitl_service)],
) -> list[HitlReviewItem]:
    return await service.list_pending()


@router.get("/reviews/{hitl_id}", response_model=HitlReviewItem)
async def get_review(
    hitl_id: UUID,
    service: Annotated[HitlService, Depends(get_hitl_service)],
) -> HitlReviewItem:
    try:
        return await service.get(hitl_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/reviews/{hitl_id}/approve", response_model=HitlReviewItem)
async def approve_review(
    hitl_id: UUID,
    request: HitlDecisionRequest,
    service: Annotated[HitlService, Depends(get_hitl_service)],
) -> HitlReviewItem:
    return await service.decide(
        hitl_id,
        status=HitlStatus.APPROVED,
        decided_by=request.decided_by,
        note=request.note,
    )


@router.post("/reviews/{hitl_id}/reject", response_model=HitlReviewItem)
async def reject_review(
    hitl_id: UUID,
    request: HitlDecisionRequest,
    service: Annotated[HitlService, Depends(get_hitl_service)],
) -> HitlReviewItem:
    return await service.decide(
        hitl_id,
        status=HitlStatus.REJECTED,
        decided_by=request.decided_by,
        note=request.note,
    )


@router.post("/reviews/{hitl_id}/escalate", response_model=HitlReviewItem)
async def escalate_review(
    hitl_id: UUID,
    request: HitlDecisionRequest,
    service: Annotated[HitlService, Depends(get_hitl_service)],
) -> HitlReviewItem:
    return await service.decide(
        hitl_id,
        status=HitlStatus.ESCALATED,
        decided_by=request.decided_by,
        note=request.note,
    )


@router.post("/reviews/{review_id}/dispute", response_model=HitlReviewItem)
async def dispute_review(
    review_id: UUID,
    request: HitlDisputeRequest,
    service: Annotated[HitlService, Depends(get_hitl_service)],
) -> HitlReviewItem:
    return await service.dispute(
        review_id,
        created_by=request.created_by,
        note=request.note,
    )

