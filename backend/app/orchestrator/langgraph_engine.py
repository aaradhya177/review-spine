from datetime import UTC, datetime

from app.core.workflow_engine import WorkflowInput, WorkflowState
from app.orchestrator.graph import build_langgraph_app, run_local_graph
from app.orchestrator.state import ReviewGraphState


class LangGraphWorkflowEngine:
    """WorkflowEngine implementation backed by LangGraph when available."""

    def __init__(self, *, use_langgraph: bool = True):
        self.use_langgraph = use_langgraph
        self._app = None
        self.states: dict[str, WorkflowState] = {}

    async def run(self, workflow_id: str, input: WorkflowInput) -> WorkflowState:
        graph_state: ReviewGraphState = {
            "workflow_id": workflow_id,
            "input": input.model_dump(mode="json"),
            "completed_nodes": [],
            "agent_results": {},
            "findings": [],
            "errors": [],
            "status": "running",
        }
        result = await self._run_graph(graph_state)
        state = self._to_workflow_state(result, input=input)
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

    async def _run_graph(self, state: ReviewGraphState) -> ReviewGraphState:
        if not self.use_langgraph:
            return await run_local_graph(state)

        try:
            if self._app is None:
                self._app = build_langgraph_app()
            return await self._app.ainvoke(state)
        except ModuleNotFoundError:
            return await run_local_graph(state)

    def _to_workflow_state(
        self,
        state: ReviewGraphState,
        *,
        input: WorkflowInput,
    ) -> WorkflowState:
        return WorkflowState(
            workflow_id=state["workflow_id"],
            status=state.get("status", "completed"),
            input=input,
            current_node=state.get("current_node"),
            completed_nodes=state.get("completed_nodes", []),
            findings=state.get("findings", []),
            errors=state.get("errors", []),
        )

