"""Dependency Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from dependency_agent.nodes.dependency_agent import dependency_agent_node
from dependency_agent.schema import DependencyAgentState


def build_dependency_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[DependencyAgentState] = StateGraph(DependencyAgentState)

    builder.add_node("dependency_agent_node", dependency_agent_node)

    builder.add_edge(START, "dependency_agent_node")
    builder.add_edge("dependency_agent_node", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
