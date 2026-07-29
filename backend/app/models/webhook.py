from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class RepositoryRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    full_name: str = Field(min_length=1)
    default_branch: str = Field(min_length=1)
    clone_url: str | None = None


class PullRequestRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    number: int = Field(ge=1)
    title: str
    head_sha: str = Field(min_length=7)
    base_sha: str = Field(min_length=7)
    draft: bool = False


class WebhookEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    delivery_id: str = Field(min_length=1)
    event_name: str = Field(min_length=1)
    action: str = Field(min_length=1)
    repository: RepositoryRef
    pull_request: PullRequestRef
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

