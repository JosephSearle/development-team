"""OrchestratorState TypedDict and supporting types for the LangGraph Orchestrator."""

from __future__ import annotations

import operator
from enum import StrEnum
from typing import Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
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


class TDDPhase(StrEnum):
    """Phase of the Red → Green → Refactor TDD state machine."""

    SETUP = "setup"
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"


class TestRunResult(TypedDict):
    """Structured output from a pytest subprocess run."""

    exit_code: int
    passed: int
    failed: int
    errors: int
    duration_seconds: float
    coverage_line_pct: float | None
    coverage_branch_pct: float | None
    failure_details: list[str]
    raw_output: str


class CodeReviewResult(TypedDict):
    """Structured output from the Code Review Agent."""

    approved: bool
    reviewer_model: str
    comments: list[str]
    blocking_issues: list[str]
    metadata: dict[str, object]


class OrchestratorState(TypedDict):
    """Full LangGraph state for the Orchestrator agent graph."""

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
    messages: Annotated[list[AnyMessage], add_messages]
    guardrail_passed: bool
