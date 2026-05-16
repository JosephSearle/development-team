"""TDD tests for the agent_router node and route_to_agent conditional edge function."""

from __future__ import annotations

import pytest
from dev_team_state import OrchestratorState, Subtask, TaskStatus
from langgraph.graph import END
from orchestrator.nodes.agent_router import agent_router, route_to_agent


def _state_with_plan(subtasks: list[Subtask]) -> OrchestratorState:
    return OrchestratorState(
        task_id="task-001",
        task_description="Test task",
        plan=subtasks,
        current_subtask=None,
        agent_results=[],
        human_approvals=[],
        run_id="run-001",
        branch_name="feat/test",
        pr_url=None,
        status=TaskStatus.IN_PROGRESS,
        messages=[],
        guardrail_passed=True,
    )


def _subtask(subtask_id: str, agent_type: str, status: str = "planning") -> Subtask:
    return Subtask(
        subtask_id=subtask_id,
        description=f"Task {subtask_id}",
        agent_type=agent_type,
        requires_approval=False,
        status=status,
    )


class TestAgentRouterSubtaskSelection:
    def test_sets_current_subtask_to_first_pending(self) -> None:
        state = _state_with_plan([
            _subtask("sub-001", "code_agent"),
            _subtask("sub-002", "test_agent"),
        ])
        result = agent_router(state)
        assert result["current_subtask"]["subtask_id"] == "sub-001"

    def test_skips_completed_subtasks(self) -> None:
        state = _state_with_plan([
            _subtask("sub-001", "code_agent", status="completed"),
            _subtask("sub-002", "test_agent"),
        ])
        result = agent_router(state)
        assert result["current_subtask"]["subtask_id"] == "sub-002"

    def test_returns_none_when_all_completed(self) -> None:
        state = _state_with_plan([
            _subtask("sub-001", "code_agent", status="completed"),
        ])
        result = agent_router(state)
        assert result["current_subtask"] is None

    def test_sets_status_completed_when_all_done(self) -> None:
        state = _state_with_plan([
            _subtask("sub-001", "code_agent", status="completed"),
        ])
        result = agent_router(state)
        assert result["status"] == TaskStatus.COMPLETED


class TestRouteToAgent:
    @pytest.mark.parametrize(
        "agent_type,expected_node",
        [
            ("code_agent", "invoke_code_agent"),
            ("test_agent", "invoke_test_agent"),
            ("code_review_agent", "invoke_code_review_agent"),
            ("git_agent", "invoke_git_agent"),
            ("architecture_agent", "invoke_architecture_agent"),
            ("cicd_agent", "invoke_cicd_agent"),
            ("security_agent", "invoke_security_agent"),
            ("docs_agent", "invoke_docs_agent"),
            ("infrastructure_agent", "invoke_infrastructure_agent"),
            ("dependency_agent", "invoke_dependency_agent"),
            ("incident_response_agent", "invoke_incident_response_agent"),
        ],
    )
    def test_routes_to_correct_node_per_agent_type(
        self, agent_type: str, expected_node: str
    ) -> None:
        state = _state_with_plan([_subtask("sub-001", agent_type)])
        state["current_subtask"] = _subtask("sub-001", agent_type)
        assert route_to_agent(state) == expected_node

    def test_routes_to_end_when_current_subtask_is_none(self) -> None:
        state = _state_with_plan([])
        state["current_subtask"] = None
        assert route_to_agent(state) == END

    def test_raises_on_unknown_agent_type(self) -> None:
        state = _state_with_plan([])
        state["current_subtask"] = _subtask("sub-001", "unknown_agent")
        with pytest.raises(ValueError, match="Unknown agent_type"):
            route_to_agent(state)
