from app.models.webhook import PullRequestRef, RepositoryRef, WebhookEvent


SUPPORTED_PULL_REQUEST_ACTIONS = {"opened", "synchronize", "reopened"}


def parse_pull_request_event(
    *,
    delivery_id: str,
    event_name: str,
    payload: dict,
) -> WebhookEvent:
    repository = payload["repository"]
    pull_request = payload["pull_request"]
    head = pull_request["head"]
    base = pull_request["base"]

    return WebhookEvent(
        delivery_id=delivery_id,
        event_name=event_name,
        action=payload["action"],
        repository=RepositoryRef(
            id=repository["id"],
            full_name=repository["full_name"],
            default_branch=repository["default_branch"],
            clone_url=repository.get("clone_url"),
        ),
        pull_request=PullRequestRef(
            id=pull_request["id"],
            number=pull_request["number"],
            title=pull_request.get("title", ""),
            head_sha=head["sha"],
            base_sha=base["sha"],
            draft=pull_request.get("draft", False),
        ),
    )

