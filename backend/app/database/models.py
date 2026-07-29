from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.models.enums import AgentType, FindingSeverity, HitlStatus, ReviewStatus


def new_uuid() -> str:
    return str(uuid4())


def now_utc() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class PrReviewRecord(Base):
    __tablename__ = "pr_review_records"
    __table_args__ = (
        UniqueConstraint(
            "repo_full_name",
            "pull_request_number",
            "head_sha",
            name="uq_pr_review_repo_pr_head",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    repo_full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    pull_request_number: Mapped[int] = mapped_column(Integer, nullable=False)
    head_sha: Mapped[str] = mapped_column(String(80), nullable=False)
    base_sha: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=ReviewStatus.QUEUED.value
    )
    overall_confidence: Mapped[float | None] = mapped_column(Float)
    routing_reason: Mapped[str | None] = mapped_column(Text)
    github_review_id: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )

    findings: Mapped[list["FindingRecord"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )
    hitl_reviews: Mapped[list["HitlReviewRecord"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )


class FindingRecord(Base):
    __tablename__ = "finding_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    review_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pr_review_records.id"), nullable=False, index=True
    )
    agent_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    line_start: Mapped[int] = mapped_column(Integer, nullable=False)
    line_end: Mapped[int | None] = mapped_column(Integer)
    suggestion: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    review: Mapped[PrReviewRecord] = relationship(back_populates="findings")

    @classmethod
    def from_domain(cls, finding: "Finding") -> "FindingRecord":
        from app.models.findings import Finding

        if not isinstance(finding, Finding):
            raise TypeError("finding must be a Finding")
        return cls(
            id=str(finding.id),
            review_id=str(finding.review_id),
            agent_type=finding.agent_type.value,
            severity=finding.severity.value,
            category=finding.category,
            summary=finding.summary,
            file_path=finding.file_path,
            line_start=finding.line_start,
            line_end=finding.line_end,
            suggestion=finding.suggestion,
            confidence=finding.confidence,
            rationale=finding.rationale,
            evidence=[item.model_dump(mode="json") for item in finding.evidence],
            created_at=finding.created_at,
        )


class HitlReviewRecord(Base):
    __tablename__ = "hitl_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    review_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pr_review_records.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=HitlStatus.PENDING.value
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    decided_by: Mapped[str | None] = mapped_column(String(255))
    decision_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    review: Mapped[PrReviewRecord] = relationship(back_populates="hitl_reviews")


class HitlFeedbackRecord(Base):
    __tablename__ = "hitl_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    review_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pr_review_records.id"), nullable=False, index=True
    )
    finding_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("finding_records.id")
    )
    feedback_type: Mapped[str] = mapped_column(String(80), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class WebhookDeliveryRecord(Base):
    __tablename__ = "webhook_deliveries"

    delivery_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    event_name: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    repo_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    pull_request_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="received")
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    scope: Mapped[str] = mapped_column(String(120), nullable=False)
    result_ref: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AgentEventRecord(Base):
    __tablename__ = "agent_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc,
        nullable=False,
        index=True,
    )
    review_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent: Mapped[str] = mapped_column(String(80), nullable=False)
    span_id: Mapped[str] = mapped_column(String(36), nullable=False, default=new_uuid)
    parent_span: Mapped[str | None] = mapped_column(String(36))
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120))
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str | None] = mapped_column(String(80))
    confidence: Mapped[float | None] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class CodeChunkRecord(Base):
    __tablename__ = "code_chunks"
    __table_args__ = (
        UniqueConstraint(
            "repo",
            "path",
            "chunk_index",
            name="code_chunks_unique_idx",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    repo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(255))
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class RepoFileIndexRecord(Base):
    __tablename__ = "repo_file_index"
    __table_args__ = (
        UniqueConstraint("repo", "path", name="repo_file_index_unique_idx"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    repo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    last_indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc,
    )


# Imported late only for type checkers/editors; runtime conversion imports inside method.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.findings import Finding
