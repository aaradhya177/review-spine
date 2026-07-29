from typing import Any, TypedDict


class ReviewGraphState(TypedDict, total=False):
    workflow_id: str
    input: dict[str, Any]
    context: dict[str, Any]
    agent_results: dict[str, list[dict[str, Any]]]
    findings: list[dict[str, Any]]
    completed_nodes: list[str]
    current_node: str
    status: str
    errors: list[str]

