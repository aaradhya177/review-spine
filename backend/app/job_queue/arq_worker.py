import logging
from typing import Any, Protocol

from app.config import Settings
from app.core.workflow_engine import StubWorkflowEngine, WorkflowEngine, WorkflowInput
from app.job_queue.contracts import ReviewJob

logger = logging.getLogger(__name__)


class JobLifecycleRecorder(Protocol):
    async def record(
        self,
        job: ReviewJob,
        *,
        status: str,
        detail: str | None = None,
    ) -> None:
        """Record worker lifecycle status for a review job."""


class InMemoryJobLifecycleRecorder:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    async def record(
        self,
        job: ReviewJob,
        *,
        status: str,
        detail: str | None = None,
    ) -> None:
        self.records.append(
            {
                "job_id": job.job_id,
                "delivery_id": job.delivery_id,
                "status": status,
                "detail": detail,
            }
        )


async def startup(ctx: dict[str, Any]) -> None:
    settings = Settings()
    ctx["settings"] = settings
    ctx.setdefault("workflow_engine", StubWorkflowEngine())
    ctx.setdefault("job_lifecycle_recorder", InMemoryJobLifecycleRecorder())
    logger.info("review worker started")


async def shutdown(ctx: dict[str, Any]) -> None:
    logger.info("review worker stopped")


async def run_review_job(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    job = ReviewJob.model_validate(payload)
    workflow_engine: WorkflowEngine = ctx.get("workflow_engine", StubWorkflowEngine())
    recorder: JobLifecycleRecorder = ctx.get(
        "job_lifecycle_recorder",
        InMemoryJobLifecycleRecorder(),
    )
    logger.info(
        "review job started",
        extra={
            "delivery_id": job.delivery_id,
            "repo": job.repo_full_name,
            "pull_request_number": job.pull_request_number,
        },
    )
    await recorder.record(job, status="started")
    try:
        workflow_input = WorkflowInput.model_validate(job.model_dump(mode="json"))
        result = await workflow_engine.run(job.job_id, workflow_input)
    except Exception as exc:
        await recorder.record(job, status="failed", detail=str(exc))
        logger.exception("review job failed", extra={"workflow_id": job.job_id})
        raise

    await recorder.record(job, status="completed")
    logger.info("review job completed", extra={"workflow_id": job.job_id})
    return result.model_dump(mode="json")


def build_redis_settings(settings: Settings | None = None) -> Any:
    from arq.connections import RedisSettings

    return RedisSettings.from_dsn((settings or Settings()).redis_url)


class WorkerSettings:
    functions = [run_review_job]
    try:
        redis_settings = build_redis_settings()
    except ModuleNotFoundError:
        redis_settings = None
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300
    max_tries = 3
    retry_jobs = True
    queue_name = "review-spine"
    allow_abort_jobs = True
