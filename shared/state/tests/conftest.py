"""Fixtures for dev-team-state tests."""

from __future__ import annotations

import pytest
from dev_team_state.schema import AgentResult, HITLApproval, OrchestratorState, Subtask, TaskStatus


@pytest.fixture()
def minimal_subtask() -> Subtask:
    return Subtask(
        subtask_id="sub-001",
        description="Write failing tests for rate limiter",
        agent_type="test_agent",
        requires_approval=False,
        status=TaskStatus.PLANNING.value,
    )


@pytest.fixture()
def minimal_agent_result() -> AgentResult:
    return AgentResult(
        agent_id="test_agent-1",
        subtask_id="sub-001",
        status=TaskStatus.COMPLETED.value,
        output="Tests written: 3 failing",
        metadata={"coverage": 0.0, "test_count": 3},
    )


@pytest.fixture()
def minimal_hitl_approval() -> HITLApproval:
    return HITLApproval(
        checkpoint_id="chk-001",
        approved=True,
        approved_by="engineer@example.com",
        timestamp="2026-05-13T10:00:00Z",
    )


@pytest.fixture()
def minimal_state(
    minimal_subtask: Subtask,
    minimal_agent_result: AgentResult,
    minimal_hitl_approval: HITLApproval,
) -> OrchestratorState:
    return OrchestratorState(
        task_id="task-001",
        task_description="Implement rate limiter middleware",
        plan=[minimal_subtask],
        current_subtask=minimal_subtask,
        agent_results=[minimal_agent_result],
        human_approvals=[minimal_hitl_approval],
        run_id="run-001",
        branch_name="feat/rate-limiter",
        pr_url=None,
        status=TaskStatus.IN_PROGRESS,
        messages=[],
        guardrail_passed=True,
    )
