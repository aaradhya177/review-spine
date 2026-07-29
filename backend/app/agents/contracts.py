from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.memory.context_retriever import RetrievedContext
from app.models.findings import Finding


class AgentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: UUID
    repo_full_name: str = Field(min_length=1)
    pull_request_number: int = Field(ge=1)
    diff_text: str = Field(min_length=1)
    changed_files: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_type: str
    findings: list[Finding] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: list[RetrievedContext] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

