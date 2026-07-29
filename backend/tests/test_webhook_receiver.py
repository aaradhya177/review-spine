import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.job_queue import InMemoryReviewQueue
from app.main import create_app
from app.webhook_receiver.router import InMemoryIdempotencyStore


SECRET = "test-webhook-secret"


def sign(body: bytes) -> str:
    digest = hmac.new(SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def pull_request_payload(action: str = "opened") -> dict:
    return {
        "action": action,
        "repository": {
            "id": 1,
            "full_name": "acme/shop",
            "default_branch": "main",
            "clone_url": "https://github.com/acme/shop.git",
        },
        "pull_request": {
            "id": 2,
            "number": 7,
            "title": "Add checkout",
            "draft": False,
            "head": {"sha": "abcdef123"},
            "base": {"sha": "123456789"},
        },
    }


def make_client() -> tuple[TestClient, InMemoryReviewQueue, InMemoryIdempotencyStore]:
    queue = InMemoryReviewQueue()
    idempotency_store = InMemoryIdempotencyStore()
    app = create_app(Settings(app_env="test", github_webhook_secret=SECRET))
    app.state.review_queue = queue
    app.state.idempotency_store = idempotency_store
    return TestClient(app), queue, idempotency_store


def post_webhook(
    client: TestClient,
    *,
    payload: dict,
    delivery_id: str = "delivery-1",
    event_name: str = "pull_request",
    signature: str | None = None,
):
    body = json.dumps(payload).encode("utf-8")
    return client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Delivery": delivery_id,
            "X-GitHub-Event": event_name,
            "X-Hub-Signature-256": signature or sign(body),
            "Content-Type": "application/json",
        },
    )


def test_valid_pull_request_webhook_enqueues_review() -> None:
    client, queue, _ = make_client()

    response = post_webhook(client, payload=pull_request_payload())

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert len(queue.jobs) == 1
    assert queue.jobs[0].repo_full_name == "acme/shop"
    assert queue.jobs[0].pull_request_number == 7


def test_invalid_signature_is_rejected() -> None:
    client, queue, _ = make_client()

    response = post_webhook(
        client,
        payload=pull_request_payload(),
        signature="sha256=bad",
    )

    assert response.status_code == 401
    assert queue.jobs == []


def test_duplicate_delivery_is_acknowledged_without_duplicate_enqueue() -> None:
    client, queue, _ = make_client()

    first = post_webhook(client, payload=pull_request_payload())
    second = post_webhook(client, payload=pull_request_payload())

    assert first.json()["status"] == "queued"
    assert second.json() == {"status": "duplicate", "delivery_id": "delivery-1"}
    assert len(queue.jobs) == 1


def test_unsupported_event_is_ignored() -> None:
    client, queue, _ = make_client()

    response = post_webhook(
        client,
        payload={"action": "created"},
        event_name="issue_comment",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert queue.jobs == []


def test_unsupported_pull_request_action_is_ignored() -> None:
    client, queue, _ = make_client()

    response = post_webhook(
        client,
        payload=pull_request_payload(action="closed"),
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ignored", "reason": "unsupported action"}
    assert queue.jobs == []

