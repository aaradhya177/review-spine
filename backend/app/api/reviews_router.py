from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/reviews", tags=["reviews"])


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    agent: str
    severity: str
    category: str
    file: str
    line: int
    summary: str
    confidence: float = Field(ge=0, le=1)
    state: str = "open"


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    repo: str
    pr: int
    title: str
    author: str
    status: str
    confidence: float = Field(ge=0, le=1)
    cost: float = Field(ge=0)
    created_at: str
    findings: list[Finding]
    decision_history: list[dict[str, str]] = []
    comments: list[dict[str, str]] = []


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decided_by: str = Field(min_length=1)
    decision: str = "dismissed"
    reason: str | None = None


class CommentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    author: str = Field(min_length=1)
    body: str = Field(min_length=1)
    finding_id: str | None = None


class SettingsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minimum_severity: str = Field(min_length=1)
    ignored_paths: list[str]
    notifications_enabled: bool


class InMemoryReviewService:
    def __init__(self) -> None:
        self.reviews: dict[str, Review] = {
            "review-1": Review(
                id="review-1", repo="acme/shop", pr=42,
                title="Refresh session tokens safely", author="Maya Chen",
                status="awaiting_human", confidence=0.61, cost=0.038,
                created_at="2026-07-30 09:20",
                findings=[
                    Finding(id="finding-1", agent="security", severity="HIGH", category="auth-bypass", file="backend/app/auth.py", line=88, summary="Role check is skipped for token refresh.", confidence=0.76),
                    Finding(id="finding-2", agent="tests", severity="MEDIUM", category="missing-test", file="backend/tests/test_auth.py", line=12, summary="No regression test covers refresh denial.", confidence=0.68),
                ],
            ),
            "review-2": Review(
                id="review-2", repo="acme/api", pr=108,
                title="Tighten request validation", author="Jon Bell",
                status="posted", confidence=0.91, cost=0.024,
                created_at="2026-07-30 08:44", findings=[],
            ),
        }
        self.settings = SettingsPayload(minimum_severity="medium", ignored_paths=["*.generated.ts", "vendor/", "fixtures/"], notifications_enabled=True)

    def get(self, review_id: str) -> Review:
        review = self.reviews.get(review_id)
        if review is None:
            raise LookupError(f"Review not found: {review_id}")
        return review

    def update(self, review: Review) -> Review:
        self.reviews[review.id] = review
        return review


_fallback_service = InMemoryReviewService()


def get_review_service(request: Request) -> InMemoryReviewService:
    return getattr(request.app.state, "review_service", _fallback_service)


Service = Annotated[InMemoryReviewService, Depends(get_review_service)]


@router.get("", response_model=list[Review])
async def list_reviews(service: Service) -> list[Review]:
    return list(service.reviews.values())


@router.get("/{review_id}", response_model=Review)
async def get_review(review_id: str, service: Service) -> Review:
    try:
        return service.get(review_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{review_id}/findings/{finding_id}/resolve", response_model=Review)
async def resolve_finding(review_id: str, finding_id: str, service: Service) -> Review:
    review = service.get(review_id)
    findings = [finding.model_copy(update={"state": "resolved"}) if finding.id == finding_id else finding for finding in review.findings]
    return service.update(review.model_copy(update={"findings": findings}))


@router.post("/{review_id}/findings/{finding_id}/dismiss", response_model=Review)
async def dismiss_finding(review_id: str, finding_id: str, request: DecisionRequest, service: Service) -> Review:
    if request.reason is None or not request.reason.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A dismissal reason is required")
    review = service.get(review_id)
    findings = [finding.model_copy(update={"state": "dismissed"}) if finding.id == finding_id else finding for finding in review.findings]
    return service.update(review.model_copy(update={"findings": findings}))


@router.post("/{review_id}/decision", response_model=Review)
async def decide_review(review_id: str, request: DecisionRequest, service: Service) -> Review:
    review = service.get(review_id)
    if request.reason is None or not request.reason.strip():
        raise HTTPException(status_code=422, detail="A decision reason is required")
    if request.decision not in {"approved", "dismissed", "rejected", "escalated"}:
        raise HTTPException(status_code=422, detail="Unsupported review decision")
    updated_status = "posted" if request.decision == "approved" else request.decision
    history = [*review.decision_history, {"action": updated_status, "by": request.decided_by, "reason": request.reason or ""}]
    return service.update(review.model_copy(update={"status": updated_status, "decision_history": history}))


@router.post("/{review_id}/comments", response_model=Review)
async def add_comment(review_id: str, request: CommentRequest, service: Service) -> Review:
    review = service.get(review_id)
    comments = [*review.comments, {"author": request.author, "body": request.body, "finding_id": request.finding_id or ""}]
    return service.update(review.model_copy(update={"comments": comments}))


@router.get("/{review_id}/trace")
async def review_trace(review_id: str, service: Service) -> list[dict[str, str]]:
    service.get(review_id)
    return [{"event": event, "status": "completed", "review_id": review_id} for event in ["webhook.received", "queue.enqueued", "orchestrator.span.start", "security.llm.call", "quality.llm.call", "aggregator.decision"]]


@router.get("/settings/current", response_model=SettingsPayload)
async def get_settings(service: Service) -> SettingsPayload:
    return service.settings


@router.put("/settings/current", response_model=SettingsPayload)
async def save_settings(payload: SettingsPayload, service: Service) -> SettingsPayload:
    if payload.minimum_severity not in {"low", "medium", "high"}:
        raise HTTPException(status_code=422, detail="Minimum severity must be low, medium, or high")
    if any(not path.strip() for path in payload.ignored_paths):
        raise HTTPException(status_code=422, detail="Ignored paths cannot be empty")
    service.settings = payload
    return service.settings
