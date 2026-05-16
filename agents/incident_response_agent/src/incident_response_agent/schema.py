"""State schema for the Incident Response Agent."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class IncidentResponseAgentState(TypedDict):
    subtask_id: str
    task_description: str
    alert_context: str
    root_cause: str
    remediation_steps: list[str]
    jira_issue_url: str | None
    runbook_path: str | None
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
