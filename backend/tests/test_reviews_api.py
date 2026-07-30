from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_review_list_and_finding_resolution() -> None:
    client = TestClient(create_app(Settings(app_env="test")))
    response = client.get("/reviews")
    assert response.status_code == 200
    assert response.json()[0]["repo"] == "acme/shop"

    response = client.post("/reviews/review-1/findings/finding-1/resolve")
    assert response.status_code == 200
    assert response.json()["findings"][0]["state"] == "resolved"


def test_dismissal_requires_reason_and_settings_persist() -> None:
    client = TestClient(create_app(Settings(app_env="test")))
    response = client.post("/reviews/review-1/findings/finding-1/dismiss", json={"decided_by": "dev"})
    assert response.status_code == 422

    response = client.put("/reviews/settings/current", json={"minimum_severity": "high", "ignored_paths": ["vendor/"], "notifications_enabled": False})
    assert response.status_code == 200
    assert response.json()["minimum_severity"] == "high"
