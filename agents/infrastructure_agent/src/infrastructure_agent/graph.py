"""Infrastructure Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from infrastructure_agent.nodes.infrastructure_agent import infrastructure_agent_node
from infrastructure_agent.schema import InfrastructureAgentState


def build_infrastructure_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[InfrastructureAgentState] = StateGraph(InfrastructureAgentState)

    builder.add_node("infrastructure_agent_node", infrastructure_agent_node)

    builder.add_edge(START, "infrastructure_agent_node")
    builder.add_edge("infrastructure_agent_node", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
