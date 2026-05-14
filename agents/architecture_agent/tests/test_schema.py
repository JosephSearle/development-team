"""Tests for ArchitectureAgentState schema."""

from __future__ import annotations

from architecture_agent.schema import ArchitectureAgentState
from langchain_core.messages import HumanMessage


class TestArchitectureAgentStateKeys:
    def test_required_keys_present(self) -> None:
        state = ArchitectureAgentState(
            subtask_id="sub-001",
            task_description="Evaluate LangGraph vs raw LangChain",
            workspace="/tmp/dev-team/sub-001",
            decision_rationale="",
            options_evaluated=[],
            adr_path=None,
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["subtask_id"] == "sub-001"
        assert "LangGraph" in state["task_description"]
        assert state["workspace"] == "/tmp/dev-team/sub-001"
        assert state["decision_rationale"] == ""
        assert state["options_evaluated"] == []
        assert state["adr_path"] is None
        assert state["messages"] == []
        assert state["status"] == "in_progress"
        assert state["error"] is None

    def test_options_evaluated_accepts_list_of_strings(self) -> None:
        state = ArchitectureAgentState(
            subtask_id="sub-002",
            task_description="Library evaluation",
            workspace="/tmp/dev-team/sub-002",
            decision_rationale="LangGraph wins on observability",
            options_evaluated=["LangGraph", "raw LangChain", "CrewAI"],
            adr_path="/tmp/dev-team/sub-002/adrs/0007-adopt-langgraph.md",
            messages=[],
            status="completed",
            error=None,
        )
        assert len(state["options_evaluated"]) == 3
        assert "LangGraph" in state["options_evaluated"]

    def test_adr_path_accepts_string(self) -> None:
        path = "/tmp/dev-team/sub-003/adrs/0008-use-postgres.md"
        state = ArchitectureAgentState(
            subtask_id="sub-003",
            task_description="Database selection",
            workspace="/tmp/dev-team/sub-003",
            decision_rationale="Postgres chosen for ACID guarantees",
            options_evaluated=["Postgres", "MySQL"],
            adr_path=path,
            messages=[],
            status="completed",
            error=None,
        )
        assert state["adr_path"] == path

    def test_messages_uses_add_messages_reducer(self) -> None:
        msg = HumanMessage(content="write an ADR")
        state = ArchitectureAgentState(
            subtask_id="sub-004",
            task_description="Test",
            workspace="/tmp/dev-team/sub-004",
            decision_rationale="",
            options_evaluated=[],
            adr_path=None,
            messages=[msg],
            status="in_progress",
            error=None,
        )
        assert len(state["messages"]) == 1

    def test_error_accepts_string(self) -> None:
        state = ArchitectureAgentState(
            subtask_id="sub-005",
            task_description="Test",
            workspace="/tmp/dev-team/sub-005",
            decision_rationale="",
            options_evaluated=[],
            adr_path=None,
            messages=[],
            status="failed",
            error="Context7 timeout during library research",
        )
        assert state["error"] == "Context7 timeout during library research"
