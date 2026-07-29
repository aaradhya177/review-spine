from copy import deepcopy
from typing import Any

from app.models.enums import AgentType
from app.orchestrator.state import ReviewGraphState


SPECIALIST_NODES = [
    "security_agent",
    "quality_agent",
    "tests_agent",
    "docs_agent",
]


def mark_completed(state: ReviewGraphState, node: str) -> ReviewGraphState:
    next_state = deepcopy(state)
    completed = list(next_state.get("completed_nodes", []))
    if node not in completed:
        completed.append(node)
    next_state["completed_nodes"] = completed
    next_state["current_node"] = node
    return next_state


async def build_context(state: ReviewGraphState) -> ReviewGraphState:
    next_state = mark_completed(state, "build_context")
    workflow_input = next_state["input"]
    next_state["context"] = {
        "repo_full_name": workflow_input["repo_full_name"],
        "head_sha": workflow_input["head_sha"],
        "base_sha": workflow_input["base_sha"],
        "retrieval_mode": "stub",
    }
    return next_state


async def run_specialist(
    state: ReviewGraphState,
    *,
    node_name: str,
    agent_type: AgentType,
) -> ReviewGraphState:
    next_state = mark_completed(state, node_name)
    agent_results = dict(next_state.get("agent_results", {}))
    agent_results[agent_type.value] = []
    next_state["agent_results"] = agent_results
    return next_state


async def security_agent(state: ReviewGraphState) -> ReviewGraphState:
    return await run_specialist(
        state,
        node_name="security_agent",
        agent_type=AgentType.SECURITY,
    )


async def quality_agent(state: ReviewGraphState) -> ReviewGraphState:
    return await run_specialist(
        state,
        node_name="quality_agent",
        agent_type=AgentType.QUALITY,
    )


async def tests_agent(state: ReviewGraphState) -> ReviewGraphState:
    return await run_specialist(
        state,
        node_name="tests_agent",
        agent_type=AgentType.TESTS,
    )


async def docs_agent(state: ReviewGraphState) -> ReviewGraphState:
    return await run_specialist(
        state,
        node_name="docs_agent",
        agent_type=AgentType.DOCS,
    )


async def aggregate(state: ReviewGraphState) -> ReviewGraphState:
    next_state = mark_completed(state, "aggregate")
    findings: list[dict[str, Any]] = []
    for agent_findings in next_state.get("agent_results", {}).values():
        findings.extend(agent_findings)
    next_state["findings"] = findings
    return next_state


async def route_result(state: ReviewGraphState) -> ReviewGraphState:
    next_state = mark_completed(state, "route_result")
    next_state["status"] = "completed"
    return next_state

