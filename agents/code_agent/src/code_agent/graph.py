"""Code Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from code_agent.nodes.code_agent import code_agent_node
from code_agent.nodes.output_guardrail import output_guardrail
from code_agent.schema import CodeAgentState


def build_code_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[CodeAgentState] = StateGraph(CodeAgentState)

    builder.add_node("code_agent_node", code_agent_node)
    builder.add_node("output_guardrail", output_guardrail)

    builder.add_edge(START, "code_agent_node")
    builder.add_edge("code_agent_node", "output_guardrail")
    builder.add_edge("output_guardrail", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
