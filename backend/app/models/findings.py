from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import AgentType, FindingSeverity


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    path: str | None = None
    symbol: str | None = None
    excerpt: str | None = None
    rank: int | None = Field(default=None, ge=1)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    review_id: UUID
    agent_type: AgentType
    severity: FindingSeverity
    category: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=500)
    file_path: str = Field(min_length=1)
    line_start: int = Field(ge=1)
    line_end: int | None = Field(default=None, ge=1)
    suggestion: str | None = Field(default=None, max_length=2000)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1, max_length=4000)
    evidence: list[Evidence] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("file_path")
    @classmethod
    def file_path_must_be_relative(cls, value: str) -> str:
        normalized = value.replace("\\", "/").strip()
        if normalized.startswith("/") or ":" in normalized:
            raise ValueError("file_path must be a repository-relative path")
        return normalized

    @model_validator(mode="after")
    def line_end_must_not_precede_start(self) -> "Finding":
        if self.line_end is not None and self.line_end < self.line_start:
            raise ValueError("line_end must be greater than or equal to line_start")
        return self

