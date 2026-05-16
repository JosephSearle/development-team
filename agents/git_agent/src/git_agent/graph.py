"""Git Agent LangGraph graph builder."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from git_agent.nodes.git_agent import git_agent_node
from git_agent.schema import GitAgentState


def build_git_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[GitAgentState] = StateGraph(GitAgentState)

    builder.add_node("git_agent_node", git_agent_node)

    builder.add_edge(START, "git_agent_node")
    builder.add_edge("git_agent_node", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
