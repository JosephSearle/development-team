"""InfrastructureAgentState TypedDict for the Infrastructure Agent LangGraph graph."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class InfrastructureAgentState(TypedDict):
    """Full LangGraph state for the Infrastructure Agent graph."""

    subtask_id: str
    task_description: str
    manifests: list[str]
    manifest_paths: list[str]
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
