"""Incident Response Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from incident_response_agent.nodes.incident_response_agent import incident_response_agent_node
from incident_response_agent.schema import IncidentResponseAgentState


def build_incident_response_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[IncidentResponseAgentState] = StateGraph(IncidentResponseAgentState)

    builder.add_node("incident_agent_node", incident_response_agent_node)

    builder.add_edge(START, "incident_agent_node")
    builder.add_edge("incident_agent_node", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
