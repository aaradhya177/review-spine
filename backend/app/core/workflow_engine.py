from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field


class WorkflowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    delivery_id: str = Field(min_length=1)
    repo_full_name: str = Field(min_length=1)
    pull_request_number: int = Field(ge=1)
    head_sha: str = Field(min_length=7)
    base_sha: str = Field(min_length=7)
    webhook_event_id: str = Field(min_length=1)


class WorkflowState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    input: WorkflowInput
    current_node: str | None = None
    completed_nodes: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorkflowEngine(Protocol):
    async def run(self, workflow_id: str, input: WorkflowInput) -> WorkflowState:
        """Start or complete a workflow run."""

    async def resume(self, workflow_id: str, state: WorkflowState) -> WorkflowState:
        """Resume a previously checkpointed workflow."""

    async def get_state(self, workflow_id: str) -> WorkflowState | None:
        """Return the latest known workflow state."""


class StubWorkflowEngine:
    """Deterministic workflow engine used until LangGraph is wired in."""

    def __init__(self) -> None:
        self.states: dict[str, WorkflowState] = {}

    async def run(self, workflow_id: str, input: WorkflowInput) -> WorkflowState:
        state = WorkflowState(
            workflow_id=workflow_id,
            status="completed",
            input=input,
            current_node="route_result",
            completed_nodes=[
                "build_context",
                "security_agent",
                "quality_agent",
                "tests_agent",
                "docs_agent",
                "aggregate",
                "route_result",
            ],
        )
        self.states[workflow_id] = state
        return state

    async def resume(self, workflow_id: str, state: WorkflowState) -> WorkflowState:
        resumed = state.model_copy(
            update={
                "workflow_id": workflow_id,
                "status": "completed",
                "updated_at": datetime.now(UTC),
            }
        )
        self.states[workflow_id] = resumed
        return resumed

    async def get_state(self, workflow_id: str) -> WorkflowState | None:
        return self.states.get(workflow_id)

