from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class GitHubReviewComment:
    path: str
    line: int
    body: str


@dataclass(frozen=True)
class GitHubReviewRequest:
    repo_full_name: str
    pull_request_number: int
    commit_id: str
    body: str
    comments: list[GitHubReviewComment]
    event: str = "COMMENT"


class GitHubTransport(Protocol):
    async def post(self, path: str, *, json: dict[str, Any]) -> dict[str, Any]:
        """POST to GitHub and return decoded JSON."""


class GitHubClient:
    def __init__(self, transport: GitHubTransport):
        self.transport = transport

    async def post_review(self, request: GitHubReviewRequest) -> str:
        owner, repo = request.repo_full_name.split("/", maxsplit=1)
        payload = {
            "commit_id": request.commit_id,
            "body": request.body,
            "event": request.event,
            "comments": [
                {
                    "path": comment.path,
                    "line": comment.line,
                    "side": "RIGHT",
                    "body": comment.body,
                }
                for comment in request.comments
            ],
        }
        response = await self.transport.post(
            f"/repos/{owner}/{repo}/pulls/{request.pull_request_number}/reviews",
            json=payload,
        )
        review_id = response.get("id")
        if review_id is None:
            raise RuntimeError("GitHub review response did not include an id")
        return str(review_id)

