import json
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.config import Settings, get_settings
from app.job_queue import InMemoryReviewQueue, ReviewJob, ReviewQueue
from app.webhook_receiver.parser import (
    SUPPORTED_PULL_REQUEST_ACTIONS,
    parse_pull_request_event,
)
from app.webhook_receiver.validator import verify_github_signature


class IdempotencyStore(Protocol):
    async def seen(self, key: str) -> bool:
        """Return whether this key has already been recorded."""

    async def record(self, key: str) -> None:
        """Record a key after accepting the delivery."""


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self.keys: set[str] = set()

    async def seen(self, key: str) -> bool:
        return key in self.keys

    async def record(self, key: str) -> None:
        self.keys.add(key)


router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_fallback_queue = InMemoryReviewQueue()
_fallback_idempotency_store = InMemoryIdempotencyStore()


def get_review_queue(request: Request) -> ReviewQueue:
    return getattr(request.app.state, "review_queue", _fallback_queue)


def get_idempotency_store(request: Request) -> IdempotencyStore:
    return getattr(request.app.state, "idempotency_store", _fallback_idempotency_store)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_delivery: Annotated[str, Header(alias="X-GitHub-Delivery")],
    x_github_event: Annotated[str, Header(alias="X-GitHub-Event")],
    x_hub_signature_256: Annotated[str, Header(alias="X-Hub-Signature-256")],
    settings: Annotated[Settings, Depends(get_settings)],
    queue: Annotated[ReviewQueue, Depends(get_review_queue)],
    idempotency_store: Annotated[IdempotencyStore, Depends(get_idempotency_store)],
) -> dict[str, str]:
    body = await request.body()
    if not settings.github_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub webhook secret is not configured",
        )

    if not verify_github_signature(
        secret=settings.github_webhook_secret,
        body=body,
        signature_header=x_hub_signature_256,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid GitHub webhook signature",
        )

    if await idempotency_store.seen(x_github_delivery):
        return {"status": "duplicate", "delivery_id": x_github_delivery}

    if x_github_event != "pull_request":
        await idempotency_store.record(x_github_delivery)
        return {"status": "ignored", "reason": "unsupported event"}

    try:
        payload = json.loads(body)
        event = parse_pull_request_event(
            delivery_id=x_github_delivery,
            event_name=x_github_event,
            payload=payload,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pull_request payload",
        ) from exc

    if event.action not in SUPPORTED_PULL_REQUEST_ACTIONS:
        await idempotency_store.record(x_github_delivery)
        return {"status": "ignored", "reason": "unsupported action"}

    job = ReviewJob(
        delivery_id=event.delivery_id,
        repo_full_name=event.repository.full_name,
        pull_request_number=event.pull_request.number,
        head_sha=event.pull_request.head_sha,
        base_sha=event.pull_request.base_sha,
        webhook_event_id=event.id,
    )
    job_id = await queue.enqueue_review(job)
    await idempotency_store.record(x_github_delivery)
    return {
        "status": "queued",
        "delivery_id": x_github_delivery,
        "job_id": job_id,
    }

