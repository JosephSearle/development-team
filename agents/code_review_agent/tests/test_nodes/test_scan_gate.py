"""Tests for the scan_gate node."""

from __future__ import annotations

from code_review_agent.nodes.scan_gate import scan_gate
from code_review_agent.schema import CodeReviewAgentState


class TestScanGateBlocked:
    def test_no_agent_results_sets_scan_complete_false(
        self, minimal_review_state: CodeReviewAgentState
    ) -> None:
        result = scan_gate(minimal_review_state)
        assert result["scan_complete"] is False

    def test_no_agent_results_sets_status_failed(
        self, minimal_review_state: CodeReviewAgentState
    ) -> None:
        result = scan_gate(minimal_review_state)
        assert result["status"] == "failed"

    def test_error_message_mentions_security_scan(
        self, minimal_review_state: CodeReviewAgentState
    ) -> None:
        result = scan_gate(minimal_review_state)
        assert "security scan" in result["error"].lower()  # type: ignore[union-attr]

    def test_non_security_agent_result_is_ignored(
        self, minimal_review_state: CodeReviewAgentState
    ) -> None:
        state = CodeReviewAgentState(
            **{
                **minimal_review_state,
                "agent_results": [
                    {
                        "agent_id": "test_agent_001",
                        "subtask_id": "sub-001",
                        "status": "completed",
                        "output": "tests pass",
                        "metadata": {"scan_complete": True},
                    }
                ],
            }
        )
        result = scan_gate(state)
        assert result["scan_complete"] is False

    def test_security_agent_without_scan_complete_is_blocked(
        self, minimal_review_state: CodeReviewAgentState
    ) -> None:
        state = CodeReviewAgentState(
            **{
                **minimal_review_state,
                "agent_results": [
                    {
                        "agent_id": "security_agent_001",
                        "subtask_id": "sub-001",
                        "status": "completed",
                        "output": "scanning",
                        "metadata": {"scan_complete": False},
                    }
                ],
            }
        )
        result = scan_gate(state)
        assert result["scan_complete"] is False


class TestScanGateAllowed:
    def test_security_agent_with_scan_complete_passes(
        self, minimal_review_state: CodeReviewAgentState
    ) -> None:
        state = CodeReviewAgentState(
            **{
                **minimal_review_state,
                "agent_results": [
                    {
                        "agent_id": "security_agent_001",
                        "subtask_id": "sub-001",
                        "status": "completed",
                        "output": "no issues",
                        "metadata": {"scan_complete": True},
                    }
                ],
            }
        )
        result = scan_gate(state)
        assert result["scan_complete"] is True

    def test_pass_returns_only_scan_complete_key(
        self, minimal_review_state: CodeReviewAgentState
    ) -> None:
        state = CodeReviewAgentState(
            **{
                **minimal_review_state,
                "agent_results": [
                    {
                        "agent_id": "security_agent_001",
                        "subtask_id": "sub-001",
                        "status": "completed",
                        "output": "ok",
                        "metadata": {"scan_complete": True},
                    }
                ],
            }
        )
        result = scan_gate(state)
        assert set(result.keys()) == {"scan_complete"}
