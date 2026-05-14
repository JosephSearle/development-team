"""CI/CD Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from cicd_agent.nodes.cicd_agent import cicd_agent_node
from cicd_agent.schema import CICDAgentState


def build_cicd_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[CICDAgentState] = StateGraph(CICDAgentState)

    builder.add_node("cicd_agent_node", cicd_agent_node)

    builder.add_edge(START, "cicd_agent_node")
    builder.add_edge("cicd_agent_node", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
