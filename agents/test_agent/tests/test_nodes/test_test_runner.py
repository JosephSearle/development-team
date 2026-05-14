"""Tests for the test_runner node."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from dev_team_state.schema import TDDPhase
from test_agent.nodes.test_runner import test_runner as _test_runner
from test_agent.schema import TestAgentState


def _make_json_report(exit_code: int, passed: int, failed: int, duration: float = 1.0) -> str:
    failures = [f"tests/test_feature.py::test_fail_{i}" for i in range(failed)]
    return json.dumps({
        "exitcode": exit_code,
        "summary": {"passed": passed, "failed": failed, "error": 0},
        "duration": duration,
        "tests": [
            {"nodeid": fid, "outcome": "failed", "call": {"longrepr": "AssertionError"}}
            for fid in failures
        ],
    })


def _make_cov_report(line_pct: float, branch_pct: float) -> str:
    return json.dumps({
        "totals": {
            "percent_covered": line_pct,
            "percent_covered_display": f"{line_pct:.0f}%",
            "covered_branches": int(branch_pct),
            "num_branches": 100,
        }
    })


@pytest.fixture()
def mock_pytest_failing(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    report = _make_json_report(exit_code=1, passed=0, failed=2)
    mock = AsyncMock(return_value=(1, f"FAILED\n{report}"))
    monkeypatch.setattr("test_agent.nodes.test_runner._run_pytest", mock)
    return mock


@pytest.fixture()
def mock_pytest_passing(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    report = _make_json_report(exit_code=0, passed=5, failed=0)
    cov = _make_cov_report(85.0, 72.0)
    mock = AsyncMock(return_value=(0, f"passed\n{report}\n{cov}"))
    monkeypatch.setattr("test_agent.nodes.test_runner._run_pytest", mock)
    return mock


class TestTestRunnerSubprocessCall:
    async def test_run_pytest_is_called(
        self, mock_pytest_failing: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        await _test_runner(red_phase_state)
        mock_pytest_failing.assert_called_once()

    async def test_run_pytest_called_with_list_starting_uv(
        self, monkeypatch: pytest.MonkeyPatch, red_phase_state: TestAgentState
    ) -> None:
        captured: list[list[str]] = []
        report = _make_json_report(exit_code=1, passed=0, failed=2)

        async def fake_run(cmd: list[str]) -> tuple[int, str]:
            captured.append(cmd)
            return (1, report)

        monkeypatch.setattr("test_agent.nodes.test_runner._run_pytest", fake_run)
        await _test_runner(red_phase_state)
        assert captured[0][0] == "uv"

    async def test_increments_run_count(
        self, mock_pytest_failing: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await _test_runner(red_phase_state)
        assert result["run_count"] == red_phase_state["run_count"] + 1


class TestTestRunnerPhaseTransitions:
    async def test_exit_nonzero_in_red_phase_stays_red(
        self, mock_pytest_failing: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await _test_runner(red_phase_state)
        assert result["tdd_phase"] == TDDPhase.RED

    async def test_exit_zero_in_red_phase_sets_rewrite_flag(
        self, mock_pytest_passing: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await _test_runner(red_phase_state)
        assert result.get("error") is not None


class TestTestRunnerResultParsing:
    async def test_parses_passed_count(
        self, monkeypatch: pytest.MonkeyPatch, red_phase_state: TestAgentState
    ) -> None:
        report = _make_json_report(exit_code=1, passed=2, failed=3)
        monkeypatch.setattr(
            "test_agent.nodes.test_runner._run_pytest", AsyncMock(return_value=(1, report))
        )
        result = await _test_runner(red_phase_state)
        assert result["test_results"]["passed"] == 2

    async def test_parses_failed_count(
        self, monkeypatch: pytest.MonkeyPatch, red_phase_state: TestAgentState
    ) -> None:
        report = _make_json_report(exit_code=1, passed=0, failed=4)
        monkeypatch.setattr(
            "test_agent.nodes.test_runner._run_pytest", AsyncMock(return_value=(1, report))
        )
        result = await _test_runner(red_phase_state)
        assert result["test_results"]["failed"] == 4

    async def test_parses_exit_code(
        self, mock_pytest_failing: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await _test_runner(red_phase_state)
        assert result["test_results"]["exit_code"] == 1

    async def test_raw_output_captured(
        self, mock_pytest_failing: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await _test_runner(red_phase_state)
        assert isinstance(result["test_results"]["raw_output"], str)
        assert len(result["test_results"]["raw_output"]) > 0


class TestTestRunnerCoverageNotPresent:
    async def test_coverage_fields_none_without_cov_data(
        self, mock_pytest_failing: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await _test_runner(red_phase_state)
        assert result["test_results"]["coverage_line_pct"] is None
        assert result["test_results"]["coverage_branch_pct"] is None
