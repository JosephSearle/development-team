"""Documentation Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from docs_agent.nodes.docs_agent import docs_agent_node
from docs_agent.schema import DocsAgentState


def build_docs_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[DocsAgentState] = StateGraph(DocsAgentState)

    builder.add_node("docs_agent_node", docs_agent_node)

    builder.add_edge(START, "docs_agent_node")
    builder.add_edge("docs_agent_node", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
