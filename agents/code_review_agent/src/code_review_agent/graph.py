"""Code Review Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from code_review_agent.nodes.reviewer import reviewer
from code_review_agent.nodes.scan_gate import scan_gate
from code_review_agent.schema import CodeReviewAgentState


def _route_after_scan_gate(state: CodeReviewAgentState) -> str:
    return "reviewer" if state.get("scan_complete") else END


def build_code_review_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[CodeReviewAgentState] = StateGraph(CodeReviewAgentState)

    builder.add_node("scan_gate", scan_gate)
    builder.add_node("reviewer", reviewer)

    builder.add_edge(START, "scan_gate")

    builder.add_conditional_edges(
        "scan_gate",
        _route_after_scan_gate,
        {"reviewer": "reviewer", END: END},
    )

    builder.add_edge("reviewer", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
