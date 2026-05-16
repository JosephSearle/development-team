"""TDD tests for the hitl_gate node.

interrupt() only fires inside a full graph execution loop, so HITL tests use a
minimal compiled sub-graph (START -> hitl_gate -> END) rather than calling the
node function directly.
"""

from __future__ import annotations

from typing import Any

from dev_team_state import OrchestratorState, Subtask, TaskStatus
from dev_team_state.schema import HITLApproval
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from orchestrator.nodes.hitl_gate import hitl_gate


def _build_hitl_graph() -> Any:
    builder: StateGraph[OrchestratorState] = StateGraph(OrchestratorState)
    builder.add_node("hitl_gate", hitl_gate)
    builder.add_edge(START, "hitl_gate")
    builder.add_edge("hitl_gate", END)
    return builder.compile(checkpointer=InMemorySaver())


def _state_with_subtask(subtask: Subtask) -> OrchestratorState:
    return OrchestratorState(
        task_id="task-001",
        task_description="Deploy feature",
        plan=[subtask],
        current_subtask=subtask,
        agent_results=[],
        human_approvals=[],
        run_id="run-001",
        branch_name="feat/deploy",
        pr_url=None,
        status=TaskStatus.IN_PROGRESS,
        messages=[],
        guardrail_passed=True,
    )


class TestHITLGateNoApprovalRequired:
    async def test_no_op_when_approval_not_required(
        self, minimal_subtask: Subtask
    ) -> None:
        graph = _build_hitl_graph()
        state = _state_with_subtask(minimal_subtask)
        config = {"configurable": {"thread_id": "no-approval-1"}}
        result = await graph.ainvoke(state, config=config)
        assert "__interrupt__" not in result
        assert result["status"] == TaskStatus.IN_PROGRESS

    async def test_human_approvals_unchanged_when_no_approval_required(
        self, minimal_subtask: Subtask
    ) -> None:
        graph = _build_hitl_graph()
        state = _state_with_subtask(minimal_subtask)
        config = {"configurable": {"thread_id": "no-approval-2"}}
        result = await graph.ainvoke(state, config=config)
        assert result["human_approvals"] == []


class TestHITLGateApprovalRequired:
    async def test_interrupt_fires_when_approval_required(
        self, approval_subtask: Subtask
    ) -> None:
        graph = _build_hitl_graph()
        state = _state_with_subtask(approval_subtask)
        config = {"configurable": {"thread_id": "approval-1"}}
        result = await graph.ainvoke(state, config=config)
        assert "__interrupt__" in result

    async def test_interrupt_payload_contains_subtask_info(
        self, approval_subtask: Subtask
    ) -> None:
        graph = _build_hitl_graph()
        state = _state_with_subtask(approval_subtask)
        config = {"configurable": {"thread_id": "approval-2"}}
        result = await graph.ainvoke(state, config=config)
        interrupt_value = result["__interrupt__"][0].value
        assert interrupt_value["subtask_id"] == approval_subtask["subtask_id"]
        assert interrupt_value["agent_type"] == approval_subtask["agent_type"]

    async def test_resume_approved_true_records_approval(
        self, approval_subtask: Subtask
    ) -> None:
        graph = _build_hitl_graph()
        state = _state_with_subtask(approval_subtask)
        config = {"configurable": {"thread_id": "approval-3"}}
        await graph.ainvoke(state, config=config)
        result = await graph.ainvoke(
            Command(resume={"approved": True, "approved_by": "eng@test.com"}),
            config=config,
        )
        assert len(result["human_approvals"]) == 1
        assert result["human_approvals"][0]["approved"] is True
        assert result["human_approvals"][0]["approved_by"] == "eng@test.com"

    async def test_resume_approved_false_records_rejection(
        self, approval_subtask: Subtask
    ) -> None:
        graph = _build_hitl_graph()
        state = _state_with_subtask(approval_subtask)
        config = {"configurable": {"thread_id": "approval-4"}}
        await graph.ainvoke(state, config=config)
        result = await graph.ainvoke(
            Command(resume={"approved": False}),
            config=config,
        )
        assert result["human_approvals"][0]["approved"] is False

    async def test_second_hitl_appends_not_replaces(
        self, approval_subtask: Subtask
    ) -> None:
        existing_approval = HITLApproval(
            checkpoint_id="chk-prior",
            approved=True,
            approved_by="prior@test.com",
            timestamp=None,
        )
        state = _state_with_subtask(approval_subtask)
        state["human_approvals"] = [existing_approval]
        graph = _build_hitl_graph()
        config = {"configurable": {"thread_id": "approval-5"}}
        await graph.ainvoke(state, config=config)
        result = await graph.ainvoke(
            Command(resume={"approved": True}),
            config=config,
        )
        assert len(result["human_approvals"]) == 2
        assert result["human_approvals"][0]["checkpoint_id"] == "chk-prior"
