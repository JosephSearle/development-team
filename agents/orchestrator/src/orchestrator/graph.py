from __future__ import annotations

from collections.abc import Callable
from typing import Any

from dev_team_state import OrchestratorState
from dev_team_state.schema import AgentResult
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from orchestrator.nodes.agent_router import _AGENT_NODE_MAP, agent_router, route_to_agent
from orchestrator.nodes.context_summariser import context_summariser
from orchestrator.nodes.hitl_gate import hitl_gate
from orchestrator.nodes.input_guardrail import input_guardrail
from orchestrator.nodes.task_planner import task_planner


def _route_after_guardrail(state: OrchestratorState) -> str:
    return "task_planner" if state["guardrail_passed"] else END


def _route_after_router(state: OrchestratorState) -> str:
    return "hitl_gate" if state["current_subtask"] is not None else END


# Stub specialist nodes — replaced by real agent invocations in Phases 3–5.
def _make_stub_agent_node(agent_id: str) -> Callable[[OrchestratorState], dict[str, Any]]:
    def _node(state: OrchestratorState) -> dict[str, Any]:
        subtask = state["current_subtask"]
        assert subtask is not None
        result = AgentResult(
            agent_id=agent_id,
            subtask_id=subtask["subtask_id"],
            status="completed",
            output=f"stub:{agent_id}",
            metadata={},
        )
        updated_plan = [
            {**s, "status": "completed"} if s["subtask_id"] == subtask["subtask_id"] else s
            for s in state["plan"]
        ]
        return {"agent_results": [result], "plan": updated_plan}

    _node.__name__ = f"invoke_{agent_id}"
    return _node


def build_orchestrator_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[OrchestratorState] = StateGraph(OrchestratorState)

    builder.add_node("input_guardrail", input_guardrail)
    builder.add_node("task_planner", task_planner)
    builder.add_node("agent_router", agent_router)
    builder.add_node("hitl_gate", hitl_gate)
    builder.add_node("context_summariser", context_summariser)

    for agent_id, node_name in _AGENT_NODE_MAP.items():
        builder.add_node(node_name, _make_stub_agent_node(agent_id))  # type: ignore[arg-type]

    builder.add_edge(START, "input_guardrail")

    builder.add_conditional_edges(
        "input_guardrail",
        _route_after_guardrail,
        {"task_planner": "task_planner", END: END},
    )

    builder.add_edge("task_planner", "agent_router")

    builder.add_conditional_edges(
        "agent_router",
        _route_after_router,
        {"hitl_gate": "hitl_gate", END: END},
    )

    builder.add_conditional_edges(
        "hitl_gate",
        route_to_agent,
        {**{node: node for node in _AGENT_NODE_MAP.values()}, END: END},
    )

    for node_name in _AGENT_NODE_MAP.values():
        builder.add_edge(node_name, "context_summariser")

    builder.add_edge("context_summariser", "agent_router")

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
