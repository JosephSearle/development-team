"""Tests for SecurityAgentState schema."""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from security_agent.schema import SecurityAgentState


class TestSecurityAgentStateKeys:
    def test_required_keys_present(self) -> None:
        state = SecurityAgentState(
            subtask_id="sub-001",
            diff_content=None,
            secrets_detected=False,
            scan_complete=False,
            sast_findings=[],
            guardrail_passed=True,
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["subtask_id"] == "sub-001"
        assert state["diff_content"] is None
        assert state["secrets_detected"] is False
        assert state["scan_complete"] is False
        assert state["sast_findings"] == []
        assert state["guardrail_passed"] is True
        assert state["messages"] == []
        assert state["status"] == "in_progress"
        assert state["error"] is None

    def test_diff_content_accepts_string(self) -> None:
        state = SecurityAgentState(
            subtask_id="sub-002",
            diff_content="+def foo():\n+    pass",
            secrets_detected=False,
            scan_complete=False,
            sast_findings=[],
            guardrail_passed=True,
            messages=[],
            status="in_progress",
            error=None,
        )
        assert "def foo" in (state["diff_content"] or "")

    def test_secrets_detected_flag(self) -> None:
        state = SecurityAgentState(
            subtask_id="sub-003",
            diff_content="+AWS_SECRET=AKIAIOSFODNN7EXAMPLE",
            secrets_detected=True,
            scan_complete=False,
            sast_findings=[],
            guardrail_passed=False,
            messages=[],
            status="failed",
            error="Secrets detected in diff",
        )
        assert state["secrets_detected"] is True
        assert state["status"] == "failed"

    def test_sast_findings_is_list(self) -> None:
        state = SecurityAgentState(
            subtask_id="sub-004",
            diff_content=None,
            secrets_detected=False,
            scan_complete=True,
            sast_findings=["SQL injection risk in query()", "XSS in render_html()"],
            guardrail_passed=True,
            messages=[],
            status="completed",
            error=None,
        )
        assert len(state["sast_findings"]) == 2

    def test_messages_accepts_list(self) -> None:
        msg = HumanMessage(content="scan this diff")
        state = SecurityAgentState(
            subtask_id="sub-005",
            diff_content=None,
            secrets_detected=False,
            scan_complete=False,
            sast_findings=[],
            guardrail_passed=True,
            messages=[msg],
            status="in_progress",
            error=None,
        )
        assert len(state["messages"]) == 1
