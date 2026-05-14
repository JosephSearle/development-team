"""State schema for the Documentation Agent."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class DocsAgentState(TypedDict):
    subtask_id: str
    task_description: str
    workspace: str
    file_paths_updated: list[str]
    changelog_entry: str
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
