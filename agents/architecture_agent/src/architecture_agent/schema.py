"""State schema for the Architecture Agent."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ArchitectureAgentState(TypedDict):
    subtask_id: str
    task_description: str
    workspace: str
    decision_rationale: str
    options_evaluated: list[str]
    adr_path: str | None
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
