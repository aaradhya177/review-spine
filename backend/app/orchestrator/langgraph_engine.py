from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.workflow_engine import WorkflowInput, WorkflowState
from app.observability.events import AgentEvent, emit_agent_event
from app.orchestrator.graph import build_langgraph_app, run_local_graph
from app.orchestrator.state import ReviewGraphState


class LangGraphWorkflowEngine:
    """WorkflowEngine implementation backed by LangGraph when available."""

    def __init__(
        self,
        *,
        use_langgraph: bool = True,
        event_session: AsyncSession | None = None,
    ):
        self.use_langgraph = use_langgraph
        self.event_session = event_session
        self._app = None
        self.states: dict[str, WorkflowState] = {}

    async def run(self, workflow_id: str, input: WorkflowInput) -> WorkflowState:
        await self._emit(input, agent="orchestrator", event_type="span.start")
        graph_state: ReviewGraphState = {
            "workflow_id": workflow_id,
            "input": input.model_dump(mode="json"),
            "completed_nodes": [],
            "agent_results": {},
            "findings": [],
            "errors": [],
            "status": "running",
        }
        try:
            result = await self._run_graph(graph_state)
            state = self._to_workflow_state(result, input=input)
        except Exception:
            await self._emit(
                input,
                agent="orchestrator",
                event_type="span.end",
                outcome="failed",
            )
            raise

        self.states[workflow_id] = state
        await self._emit(
            input,
            agent="orchestrator",
            event_type="span.end",
            outcome=state.status,
        )
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

    async def _emit(
        self,
        input: WorkflowInput,
        *,
        agent: str,
        event_type: str,
        outcome: str | None = None,
    ) -> None:
        if self.event_session is None:
            return
        await emit_agent_event(
            self.event_session,
            AgentEvent(
                review_id=input.webhook_event_id,
                agent=agent,
                event_type=event_type,
                outcome=outcome,
                payload={
                    "delivery_id": input.delivery_id,
                    "repo_full_name": input.repo_full_name,
                    "pull_request_number": input.pull_request_number,
                },
            ),
        )
