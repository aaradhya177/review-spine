from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delivery_id: str = Field(min_length=1)
    repo_full_name: str = Field(min_length=1)
    pull_request_number: int = Field(ge=1)
    head_sha: str = Field(min_length=7)
    base_sha: str = Field(min_length=7)
    webhook_event_id: UUID

    @property
    def job_id(self) -> str:
        return f"review:{self.delivery_id}"


class ReviewQueue(Protocol):
    async def enqueue_review(self, job: ReviewJob) -> str:
        """Enqueue review work and return a queue job identifier."""


class InMemoryReviewQueue:
    def __init__(self) -> None:
        self.jobs: list[ReviewJob] = []

    async def enqueue_review(self, job: ReviewJob) -> str:
        self.jobs.append(job)
        return job.job_id
