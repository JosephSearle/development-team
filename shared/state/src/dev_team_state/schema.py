"""OrchestratorState TypedDict and supporting types for the LangGraph Orchestrator."""

from __future__ import annotations

import operator
from enum import StrEnum
from typing import Annotated

from langchain_core.messages import AnyMessage
from typing_extensions import TypedDict


class TaskStatus(StrEnum):
    """Lifecycle status of an orchestrator task."""

    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class Subtask(TypedDict):
    """A single unit of work delegated to a specialist agent."""

    subtask_id: str
    description: str
    agent_type: str
    requires_approval: bool
    status: str


class AgentResult(TypedDict):
    """Structured result returned by a specialist agent after completing a subtask."""

    agent_id: str
    subtask_id: str
    status: str
    output: str
    metadata: dict[str, object]


class HITLApproval(TypedDict):
    """Record of a human-in-the-loop approval decision."""

    checkpoint_id: str
    approved: bool
    approved_by: str | None
    timestamp: str | None


class OrchestratorState(TypedDict):
    """Full LangGraph state for the Orchestrator agent graph.

    Fields annotated with operator.add use the LangGraph reducer pattern —
    new list values are appended rather than replaced. Required for
    agent_results and messages which accumulate across sub-agent executions.
    """

    task_id: str
    task_description: str
    plan: list[Subtask]
    current_subtask: Subtask | None
    agent_results: Annotated[list[AgentResult], operator.add]
    human_approvals: list[HITLApproval]
    run_id: str
    branch_name: str
    pr_url: str | None
    status: TaskStatus
    messages: Annotated[list[AnyMessage], operator.add]
    guardrail_passed: bool
