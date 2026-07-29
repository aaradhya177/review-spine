import hashlib
import hmac
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.job_queue import InMemoryReviewQueue
from app.main import create_app
from app.webhook_receiver.router import InMemoryIdempotencyStore


SECRET = "local-demo-secret"


def sign(body: bytes) -> str:
    digest = hmac.new(SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def run_demo() -> dict:
    fixture = Path("fixtures/pull_request_opened.json")
    body = fixture.read_bytes()
    queue = InMemoryReviewQueue()
    idempotency = InMemoryIdempotencyStore()
    app = create_app(Settings(app_env="test", github_webhook_secret=SECRET))
    app.state.review_queue = queue
    app.state.idempotency_store = idempotency
    client = TestClient(app)
    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-GitHub-Delivery": "demo-delivery-1",
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": sign(body),
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()
    return {
        "response": response.json(),
        "queued_jobs": [job.model_dump(mode="json") for job in queue.jobs],
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))

