"""TDD tests for OrchestratorState TypedDict schema.

Written BEFORE schema.py (Red phase). Verifies structural shape only:
key names, enum values, reducer declarations, instantiation, and None-ability.
"""

from __future__ import annotations

import operator
from typing import get_type_hints

from dev_team_state.schema import (
    AgentResult,
    HITLApproval,
    OrchestratorState,
    Subtask,
    TaskStatus,
)


class TestTaskStatus:
    def test_all_five_values_defined(self) -> None:
        assert len(TaskStatus) == 5

    def test_values_are_correct_strings(self) -> None:
        assert TaskStatus.PLANNING.value == "planning"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.AWAITING_APPROVAL.value == "awaiting_approval"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_is_str_subclass(self) -> None:
        assert issubclass(TaskStatus, str)


class TestSubtask:
    def test_all_keys_present(self) -> None:
        assert set(Subtask.__annotations__) == {
            "subtask_id",
            "description",
            "agent_type",
            "requires_approval",
            "status",
        }

    def test_subtask_id_is_str(self) -> None:
        assert get_type_hints(Subtask)["subtask_id"] is str

    def test_requires_approval_is_bool(self) -> None:
        assert get_type_hints(Subtask)["requires_approval"] is bool

    def test_instantiable(self, minimal_subtask: Subtask) -> None:
        assert minimal_subtask["subtask_id"] == "sub-001"
        assert minimal_subtask["requires_approval"] is False


class TestAgentResult:
    def test_all_keys_present(self) -> None:
        assert set(AgentResult.__annotations__) == {
            "agent_id",
            "subtask_id",
            "status",
            "output",
            "metadata",
        }

    def test_instantiable(self, minimal_agent_result: AgentResult) -> None:
        assert minimal_agent_result["agent_id"] == "test_agent-1"

    def test_metadata_accepts_mixed_value_types(self, minimal_agent_result: AgentResult) -> None:
        assert isinstance(minimal_agent_result["metadata"], dict)
        assert minimal_agent_result["metadata"]["test_count"] == 3


class TestHITLApproval:
    def test_all_keys_present(self) -> None:
        assert set(HITLApproval.__annotations__) == {
            "checkpoint_id",
            "approved",
            "approved_by",
            "timestamp",
        }

    def test_approved_is_bool_annotation(self) -> None:
        assert get_type_hints(HITLApproval)["approved"] is bool

    def test_approved_by_accepts_none(self) -> None:
        approval = HITLApproval(
            checkpoint_id="chk-002",
            approved=False,
            approved_by=None,
            timestamp=None,
        )
        assert approval["approved_by"] is None
        assert approval["timestamp"] is None

    def test_instantiable(self, minimal_hitl_approval: HITLApproval) -> None:
        assert minimal_hitl_approval["checkpoint_id"] == "chk-001"
        assert minimal_hitl_approval["approved"] is True


class TestOrchestratorState:
    EXPECTED_KEYS = {
        "task_id",
        "task_description",
        "plan",
        "current_subtask",
        "agent_results",
        "human_approvals",
        "run_id",
        "branch_name",
        "pr_url",
        "status",
        "messages",
        "guardrail_passed",
    }

    def test_all_keys_present(self) -> None:
        assert set(OrchestratorState.__annotations__) == self.EXPECTED_KEYS

    def test_instantiable_with_all_fields(self, minimal_state: OrchestratorState) -> None:
        assert minimal_state["task_id"] == "task-001"
        assert minimal_state["status"] == TaskStatus.IN_PROGRESS
        assert minimal_state["guardrail_passed"] is True

    def test_current_subtask_accepts_none(self) -> None:
        state = OrchestratorState(
            task_id="t",
            task_description="d",
            plan=[],
            current_subtask=None,
            agent_results=[],
            human_approvals=[],
            run_id="r",
            branch_name="b",
            pr_url=None,
            status=TaskStatus.PLANNING,
            messages=[],
            guardrail_passed=False,
        )
        assert state["current_subtask"] is None

    def test_pr_url_accepts_none(self, minimal_state: OrchestratorState) -> None:
        assert minimal_state["pr_url"] is None

    def test_status_accepts_task_status_enum(self, minimal_state: OrchestratorState) -> None:
        assert minimal_state["status"] == TaskStatus.IN_PROGRESS

    def test_guardrail_passed_is_bool(self, minimal_state: OrchestratorState) -> None:
        assert isinstance(minimal_state["guardrail_passed"], bool)

    def test_plan_accepts_multiple_subtasks(self, minimal_subtask: Subtask) -> None:
        subtask_2 = Subtask(
            subtask_id="sub-002",
            description="Write implementation",
            agent_type="code_agent",
            requires_approval=False,
            status=TaskStatus.PLANNING.value,
        )
        state = OrchestratorState(
            task_id="t",
            task_description="d",
            plan=[minimal_subtask, subtask_2],
            current_subtask=minimal_subtask,
            agent_results=[],
            human_approvals=[],
            run_id="r",
            branch_name="b",
            pr_url=None,
            status=TaskStatus.PLANNING,
            messages=[],
            guardrail_passed=True,
        )
        assert len(state["plan"]) == 2

    def test_agent_results_reducer_semantics(self, minimal_agent_result: AgentResult) -> None:
        """operator.add on two lists appends — the LangGraph reducer contract."""
        existing = [minimal_agent_result]
        new_result = AgentResult(
            agent_id="code_agent-1",
            subtask_id="sub-002",
            status="completed",
            output="Code written",
            metadata={},
        )
        combined = operator.add(existing, [new_result])
        assert len(combined) == 2
        assert combined[1]["agent_id"] == "code_agent-1"

    def test_messages_field_is_list(self, minimal_state: OrchestratorState) -> None:
        assert isinstance(minimal_state["messages"], list)

    def test_messages_reducer_is_add_messages(self) -> None:
        import typing
        from langgraph.graph.message import add_messages
        hints = typing.get_type_hints(OrchestratorState, include_extras=True)
        args = typing.get_args(hints["messages"])
        assert args[1] is add_messages
