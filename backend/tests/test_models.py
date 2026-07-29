from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import (
    AgentType,
    Evidence,
    Finding,
    FindingSeverity,
    PullRequestRef,
    RepositoryRef,
    Review,
    ReviewStatus,
    WebhookEvent,
)


def make_finding(**overrides: object) -> Finding:
    payload = {
        "review_id": uuid4(),
        "agent_type": AgentType.SECURITY,
        "severity": FindingSeverity.HIGH,
        "category": "sql-injection",
        "summary": "Unsafe SQL query uses request input.",
        "file_path": "backend/app/search.py",
        "line_start": 42,
        "line_end": 43,
        "suggestion": "Use bind parameters.",
        "confidence": 0.87,
        "rationale": "The changed line formats user input into SQL.",
        "evidence": [Evidence(source="retrieval", path="backend/app/search.py", rank=1)],
    }
    payload.update(overrides)
    return Finding(**payload)


def test_finding_serializes_to_stable_json_shape() -> None:
    finding = make_finding()

    dumped = finding.model_dump(mode="json")

    assert dumped["agent_type"] == "security"
    assert dumped["severity"] == "HIGH"
    assert dumped["confidence"] == 0.87
    assert dumped["file_path"] == "backend/app/search.py"
    assert dumped["evidence"][0]["source"] == "retrieval"


def test_finding_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        make_finding(confidence=1.1)


def test_finding_rejects_absolute_file_path() -> None:
    with pytest.raises(ValidationError):
        make_finding(file_path="C:/repo/backend/app/search.py")


def test_finding_normalizes_windows_path_separator() -> None:
    finding = make_finding(file_path="backend\\app\\search.py")

    assert finding.file_path == "backend/app/search.py"


def test_finding_rejects_line_end_before_start() -> None:
    with pytest.raises(ValidationError):
        make_finding(line_start=50, line_end=49)


def test_severity_rank_orders_critical_above_info() -> None:
    assert FindingSeverity.CRITICAL.rank > FindingSeverity.INFO.rank


def test_review_can_contain_findings() -> None:
    finding = make_finding()
    review = Review(
        repo_full_name="acme/shop",
        pull_request_number=12,
        status=ReviewStatus.RUNNING,
        findings=[finding],
        overall_confidence=0.87,
    )

    assert review.findings == [finding]
    assert review.status == ReviewStatus.RUNNING


def test_webhook_event_contract() -> None:
    event = WebhookEvent(
        delivery_id="delivery-1",
        event_name="pull_request",
        action="opened",
        repository=RepositoryRef(
            id=1,
            full_name="acme/shop",
            default_branch="main",
            clone_url="https://github.com/acme/shop.git",
        ),
        pull_request=PullRequestRef(
            id=2,
            number=3,
            title="Add checkout",
            head_sha="abcdef123",
            base_sha="123456789",
        ),
    )

    assert event.repository.full_name == "acme/shop"
    assert event.pull_request.number == 3

