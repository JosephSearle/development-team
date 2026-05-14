"""Security Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from security_agent.nodes.output_guardrail import output_guardrail
from security_agent.nodes.sast_agent import sast_agent_node
from security_agent.nodes.secrets_scanner import secrets_scanner
from security_agent.schema import SecurityAgentState


def _route_after_secrets(
    state: SecurityAgentState,
) -> Literal["sast_agent_node", "__end__"]:
    if state.get("secrets_detected"):
        return "__end__"
    return "sast_agent_node"


def build_security_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[SecurityAgentState] = StateGraph(SecurityAgentState)

    builder.add_node("secrets_scanner", secrets_scanner)
    builder.add_node("sast_agent_node", sast_agent_node)
    builder.add_node("output_guardrail", output_guardrail)

    builder.add_edge(START, "secrets_scanner")
    builder.add_conditional_edges("secrets_scanner", _route_after_secrets)
    builder.add_edge("sast_agent_node", "output_guardrail")
    builder.add_edge("output_guardrail", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
