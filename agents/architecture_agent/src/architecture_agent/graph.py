"""Architecture Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from architecture_agent.nodes.architecture_agent import architecture_agent_node
from architecture_agent.schema import ArchitectureAgentState


def build_architecture_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[ArchitectureAgentState] = StateGraph(ArchitectureAgentState)

    builder.add_node("architecture_agent_node", architecture_agent_node)

    builder.add_edge(START, "architecture_agent_node")
    builder.add_edge("architecture_agent_node", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
