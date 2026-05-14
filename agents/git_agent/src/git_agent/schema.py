"""GitAgentState TypedDict for the Git Agent LangGraph graph."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class GitAgentState(TypedDict):
    """Full LangGraph state for the Git Agent graph."""

    subtask_id: str
    task_description: str
    branch_name: str
    pr_url: str | None
    commit_messages: list[str]
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
