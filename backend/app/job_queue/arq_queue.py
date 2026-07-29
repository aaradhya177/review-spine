from typing import Any

from app.job_queue.contracts import ReviewJob


class ARQReviewQueue:
    """Review queue backed by ARQ.

    The redis pool is injected to keep this class easy to test and to avoid
    importing ARQ from modules that only need the queue contract.
    """

    def __init__(self, redis_pool: Any, *, queue_name: str = "review-spine"):
        self.redis_pool = redis_pool
        self.queue_name = queue_name

    async def enqueue_review(self, job: ReviewJob) -> str:
        await self.redis_pool.enqueue_job(
            "run_review_job",
            job.model_dump(mode="json"),
            _job_id=job.job_id,
            _queue_name=self.queue_name,
            _defer_by=None,
        )
        return job.job_id


async def create_arq_review_queue(
    redis_url: str,
    *,
    queue_name: str = "review-spine",
) -> ARQReviewQueue:
    from arq.connections import RedisSettings, create_pool

    redis_settings = RedisSettings.from_dsn(redis_url)
    redis_pool = await create_pool(redis_settings)
    return ARQReviewQueue(redis_pool, queue_name=queue_name)

