"""CICDAgentState TypedDict for the CI/CD Agent LangGraph graph."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class CICDAgentState(TypedDict):
    """Full LangGraph state for the CI/CD Agent graph."""

    subtask_id: str
    task_description: str
    pipeline_type: str | None
    build_url: str | None
    deployment_env: str | None
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
