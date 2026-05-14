"""State schema for the Dependency Agent."""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class DependencyAgentState(TypedDict):
    subtask_id: str
    task_description: str
    dependencies_scanned: list[str]
    vulnerabilities_found: list[str]
    upgrades_proposed: list[str]
    pr_urls: list[str]
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
