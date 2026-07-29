from uuid import uuid4

import pytest

from app.integrations import (
    GitHubClient,
    GitHubReviewComment,
    GitHubReviewRequest,
    format_github_review,
)
from app.models.enums import AgentType, FindingSeverity
from app.models.findings import Finding


class FakeTransport:
    def __init__(self, response: dict):
        self.response = response
        self.calls = []

    async def post(self, path: str, *, json: dict):
        self.calls.append({"path": path, "json": json})
        return self.response


def make_finding() -> Finding:
    return Finding(
        review_id=uuid4(),
        agent_type=AgentType.QUALITY,
        severity=FindingSeverity.HIGH,
        category="edge-case",
        summary="Missing empty-input handling.",
        file_path="app.py",
        line_start=12,
        suggestion="Handle empty input before processing.",
        confidence=0.88,
        rationale="The function indexes the first element without checking length.",
    )


def test_format_github_review_maps_findings_to_inline_comments() -> None:
    body, comments = format_github_review([make_finding()])

    assert "actionable issues" in body
    assert comments[0]["path"] == "app.py"
    assert comments[0]["line"] == 12
    assert "HIGH / edge-case" in comments[0]["body"]


@pytest.mark.asyncio
async def test_github_client_posts_review_payload() -> None:
    transport = FakeTransport({"id": 123})
    client = GitHubClient(transport)

    review_id = await client.post_review(
        GitHubReviewRequest(
            repo_full_name="acme/shop",
            pull_request_number=7,
            commit_id="abcdef123",
            body="Review body",
            comments=[
                GitHubReviewComment(path="app.py", line=12, body="Comment body")
            ],
        )
    )

    assert review_id == "123"
    assert transport.calls[0]["path"] == "/repos/acme/shop/pulls/7/reviews"
    assert transport.calls[0]["json"]["comments"][0]["side"] == "RIGHT"


@pytest.mark.asyncio
async def test_github_client_requires_review_id_response() -> None:
    client = GitHubClient(FakeTransport({}))

    with pytest.raises(RuntimeError, match="did not include an id"):
        await client.post_review(
            GitHubReviewRequest(
                repo_full_name="acme/shop",
                pull_request_number=7,
                commit_id="abcdef123",
                body="Review body",
                comments=[],
            )
        )

