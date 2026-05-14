"""SecurityAgentState TypedDict for the Security Agent LangGraph graph."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class SecurityAgentState(TypedDict):
    """Full LangGraph state for the Security Agent graph."""

    subtask_id: str
    diff_content: str | None
    secrets_detected: bool
    scan_complete: bool
    sast_findings: list[str]
    guardrail_passed: bool
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
