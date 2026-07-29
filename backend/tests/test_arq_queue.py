from uuid import uuid4

import pytest

from app.core.workflow_engine import WorkflowInput, WorkflowState
from app.job_queue import ARQReviewQueue, ReviewJob
from app.job_queue.arq_worker import InMemoryJobLifecycleRecorder, run_review_job


def make_job() -> ReviewJob:
    return ReviewJob(
        delivery_id="delivery-1",
        repo_full_name="acme/shop",
        pull_request_number=7,
        head_sha="abcdef123",
        base_sha="123456789",
        webhook_event_id=uuid4(),
    )


class FakeRedisPool:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def enqueue_job(self, function: str, payload: dict, **kwargs):
        self.calls.append({"function": function, "payload": payload, "kwargs": kwargs})


class FakeWorkflowRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def run(self, workflow_id: str, input: WorkflowInput) -> WorkflowState:
        self.calls.append((workflow_id, input))
        return WorkflowState(workflow_id=workflow_id, status="done", input=input)

    async def resume(self, workflow_id: str, state: WorkflowState) -> WorkflowState:
        return state

    async def get_state(self, workflow_id: str) -> WorkflowState | None:
        return None


class FailingWorkflowRunner:
    async def run(self, workflow_id: str, input: WorkflowInput) -> WorkflowState:
        raise RuntimeError("workflow exploded")

    async def resume(self, workflow_id: str, state: WorkflowState) -> WorkflowState:
        return state

    async def get_state(self, workflow_id: str) -> WorkflowState | None:
        return None


@pytest.mark.asyncio
async def test_arq_queue_enqueues_stable_job_payload() -> None:
    redis_pool = FakeRedisPool()
    queue = ARQReviewQueue(redis_pool)
    job = make_job()

    job_id = await queue.enqueue_review(job)

    assert job_id == "review:delivery-1"
    assert redis_pool.calls[0]["function"] == "run_review_job"
    assert redis_pool.calls[0]["payload"]["repo_full_name"] == "acme/shop"
    assert redis_pool.calls[0]["kwargs"]["_job_id"] == "review:delivery-1"
    assert redis_pool.calls[0]["kwargs"]["_queue_name"] == "review-spine"


@pytest.mark.asyncio
async def test_worker_passes_job_to_workflow_runner() -> None:
    runner = FakeWorkflowRunner()
    recorder = InMemoryJobLifecycleRecorder()
    job = make_job()

    result = await run_review_job(
        {"workflow_engine": runner, "job_lifecycle_recorder": recorder},
        job.model_dump(mode="json"),
    )

    assert result["workflow_id"] == "review:delivery-1"
    assert result["status"] == "done"
    assert runner.calls[0][0] == "review:delivery-1"
    assert runner.calls[0][1].pull_request_number == 7
    assert [record["status"] for record in recorder.records] == ["started", "completed"]


@pytest.mark.asyncio
async def test_worker_records_failure_before_retry_or_dead_letter() -> None:
    recorder = InMemoryJobLifecycleRecorder()
    job = make_job()

    with pytest.raises(RuntimeError, match="workflow exploded"):
        await run_review_job(
            {
                "workflow_runner": FailingWorkflowRunner(),
                "workflow_engine": FailingWorkflowRunner(),
                "job_lifecycle_recorder": recorder,
            },
            job.model_dump(mode="json"),
        )

    assert [record["status"] for record in recorder.records] == ["started", "failed"]
    assert recorder.records[-1]["detail"] == "workflow exploded"
