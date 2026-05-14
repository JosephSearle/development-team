"""Tests for the coverage_checker node."""

from __future__ import annotations

import pytest
from dev_team_state.schema import TDDPhase, TestRunResult
from test_agent.nodes.coverage_checker import coverage_checker
from test_agent.schema import TestAgentState


def _state_with_coverage(line_pct: float | None, branch_pct: float | None) -> TestAgentState:
    results = TestRunResult(
        exit_code=0,
        passed=5,
        failed=0,
        errors=0,
        duration_seconds=1.0,
        coverage_line_pct=line_pct,
        coverage_branch_pct=branch_pct,
        failure_details=[],
        raw_output="5 passed",
    )
    return TestAgentState(
        subtask_id="sub-001",
        feature_spec="spec",
        tdd_phase=TDDPhase.RED,
        test_file_path="/tmp/test.py",
        test_code="...",
        test_results=results,
        run_count=1,
        flaky_test_ids=[],
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
    )


class TestCoverageCheckerPass:
    def test_no_op_when_test_results_none(self, minimal_test_agent_state: TestAgentState) -> None:
        result = coverage_checker(minimal_test_agent_state)
        assert result == {}

    def test_passes_when_line_and_branch_above_threshold(self) -> None:
        state = _state_with_coverage(85.0, 75.0)
        result = coverage_checker(state)
        assert result["tdd_phase"] == TDDPhase.GREEN

    def test_passes_at_exact_threshold(self) -> None:
        state = _state_with_coverage(80.0, 70.0)
        result = coverage_checker(state)
        assert result["tdd_phase"] == TDDPhase.GREEN

    def test_returns_only_tdd_phase_on_pass(self) -> None:
        state = _state_with_coverage(90.0, 80.0)
        result = coverage_checker(state)
        assert set(result.keys()) == {"tdd_phase"}


class TestCoverageCheckerFail:
    def test_fails_when_line_below_80(self) -> None:
        state = _state_with_coverage(79.9, 75.0)
        result = coverage_checker(state)
        assert result["status"] == "failed"

    def test_fails_when_branch_below_70(self) -> None:
        state = _state_with_coverage(85.0, 69.9)
        result = coverage_checker(state)
        assert result["status"] == "failed"

    def test_error_message_includes_actual_coverage(self) -> None:
        state = _state_with_coverage(79.9, 65.0)
        result = coverage_checker(state)
        assert "79.9" in result["error"] or "79" in result["error"]


class TestCoverageCheckerThresholds:
    def test_thresholds_configurable_via_monkeypatch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import test_agent.nodes.coverage_checker as mod
        monkeypatch.setattr(mod, "LINE_COVERAGE_THRESHOLD", 50.0)
        monkeypatch.setattr(mod, "BRANCH_COVERAGE_THRESHOLD", 40.0)
        state = _state_with_coverage(51.0, 41.0)
        result = coverage_checker(state)
        assert result["tdd_phase"] == TDDPhase.GREEN
