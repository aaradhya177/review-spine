from collections.abc import Callable
from typing import Awaitable

from app.orchestrator import nodes
from app.orchestrator.state import ReviewGraphState

Node = Callable[[ReviewGraphState], Awaitable[ReviewGraphState]]


def get_node_sequence() -> list[Node]:
    return [
        nodes.build_context,
        nodes.security_agent,
        nodes.quality_agent,
        nodes.tests_agent,
        nodes.docs_agent,
        nodes.aggregate,
        nodes.route_result,
    ]


async def run_local_graph(state: ReviewGraphState) -> ReviewGraphState:
    next_state = state
    for node in get_node_sequence():
        next_state = await node(next_state)
    return next_state


def build_langgraph_app():
    """Build the real LangGraph app when the dependency is installed."""

    from langgraph.graph import END, StateGraph

    graph = StateGraph(ReviewGraphState)
    graph.add_node("build_context", nodes.build_context)
    graph.add_node("security_agent", nodes.security_agent)
    graph.add_node("quality_agent", nodes.quality_agent)
    graph.add_node("tests_agent", nodes.tests_agent)
    graph.add_node("docs_agent", nodes.docs_agent)
    graph.add_node("aggregate", nodes.aggregate)
    graph.add_node("route_result", nodes.route_result)

    graph.set_entry_point("build_context")
    graph.add_edge("build_context", "security_agent")
    graph.add_edge("security_agent", "quality_agent")
    graph.add_edge("quality_agent", "tests_agent")
    graph.add_edge("tests_agent", "docs_agent")
    graph.add_edge("docs_agent", "aggregate")
    graph.add_edge("aggregate", "route_result")
    graph.add_edge("route_result", END)
    return graph.compile()

