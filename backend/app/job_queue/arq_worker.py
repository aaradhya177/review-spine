import logging
from typing import Any, Protocol

from app.config import Settings
from app.job_queue.contracts import ReviewJob

logger = logging.getLogger(__name__)


class WorkflowRunner(Protocol):
    async def run(self, workflow_id: str, input: dict[str, Any]) -> dict[str, Any]:
        """Run review workflow and return serializable state."""


class PlaceholderWorkflowRunner:
    async def run(self, workflow_id: str, input: dict[str, Any]) -> dict[str, Any]:
        logger.info("placeholder workflow accepted job", extra={"workflow_id": workflow_id})
        return {
            "workflow_id": workflow_id,
            "status": "accepted",
            "input": input,
        }


async def startup(ctx: dict[str, Any]) -> None:
    settings = Settings()
    ctx["settings"] = settings
    ctx.setdefault("workflow_runner", PlaceholderWorkflowRunner())
    logger.info("review worker started")


async def shutdown(ctx: dict[str, Any]) -> None:
    logger.info("review worker stopped")


async def run_review_job(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    job = ReviewJob.model_validate(payload)
    runner: WorkflowRunner = ctx.get("workflow_runner", PlaceholderWorkflowRunner())
    logger.info(
        "review job started",
        extra={
            "delivery_id": job.delivery_id,
            "repo": job.repo_full_name,
            "pull_request_number": job.pull_request_number,
        },
    )
    result = await runner.run(job.job_id, job.model_dump(mode="json"))
    logger.info("review job completed", extra={"workflow_id": job.job_id})
    return result


class WorkerSettings:
    functions = [run_review_job]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300
    max_tries = 3
    retry_jobs = True
    queue_name = "review-spine"

