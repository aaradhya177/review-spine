from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import Settings
from app.hitl import HitlReviewItem, InMemoryHitlService
from app.main import create_app
from app.models.enums import HitlStatus


def make_client():
    item = HitlReviewItem(
        id=uuid4(),
        review_id=uuid4(),
        status=HitlStatus.PENDING,
        reason="low confidence",
    )
    service = InMemoryHitlService([item])
    app = create_app(Settings(app_env="test"))
    app.state.hitl_service = service
    return TestClient(app), service, item


def test_list_pending_hitl_reviews() -> None:
    client, _service, item = make_client()

    response = client.get("/hitl/reviews")

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(item.id)


def test_approve_hitl_review() -> None:
    client, service, item = make_client()

    response = client.post(
        f"/hitl/reviews/{item.id}/approve",
        json={"decided_by": "senior@example.com", "note": "looks good"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert service.decisions[0]["decided_by"] == "senior@example.com"


def test_dispute_review_creates_disputed_item() -> None:
    client, service, item = make_client()

    response = client.post(
        f"/hitl/reviews/{item.review_id}/dispute",
        json={"created_by": "dev@example.com", "note": "false positive"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "disputed"
    assert service.disputes[0]["note"] == "false positive"

