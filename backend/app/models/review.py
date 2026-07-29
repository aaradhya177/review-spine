from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReviewStatus
from app.models.findings import Finding


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    repo_full_name: str = Field(min_length=1)
    pull_request_number: int = Field(ge=1)
    status: ReviewStatus = ReviewStatus.QUEUED
    findings: list[Finding] = Field(default_factory=list)
    overall_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    routing_reason: str | None = None
    github_review_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

