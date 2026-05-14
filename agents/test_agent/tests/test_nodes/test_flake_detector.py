"""Tests for the flake_detector node."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from dev_team_state.schema import TDDPhase
from test_agent.nodes.flake_detector import flake_detector
from test_agent.schema import TestAgentState


def _make_run_result(exit_code: int, failure_ids: list[str]) -> tuple[int, str]:
    import json
    tests = [
        {"nodeid": fid, "outcome": "failed"} for fid in failure_ids
    ]
    report = json.dumps({
        "exitcode": exit_code,
        "summary": {"failed": len(failure_ids)},
        "tests": tests,
    })
    return (exit_code, report)


@pytest.fixture()
def mock_all_consistent_failures(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """All 3 runs fail the same tests — no flakes."""
    mock = AsyncMock(side_effect=[
        _make_run_result(1, ["test_a", "test_b"]),
        _make_run_result(1, ["test_a", "test_b"]),
        _make_run_result(1, ["test_a", "test_b"]),
    ])
    monkeypatch.setattr("test_agent.nodes.flake_detector._run_pytest", mock)
    return mock


@pytest.fixture()
def mock_one_flaky_run(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """test_a fails only in run 2 — it's flaky."""
    mock = AsyncMock(side_effect=[
        _make_run_result(1, ["test_b"]),
        _make_run_result(1, ["test_a", "test_b"]),
        _make_run_result(1, ["test_b"]),
    ])
    monkeypatch.setattr("test_agent.nodes.flake_detector._run_pytest", mock)
    return mock


class TestFlakeDetectorNoFlakes:
    async def test_no_flaky_tests_when_all_consistent(
        self, mock_all_consistent_failures: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await flake_detector(red_phase_state)
        assert result["flaky_test_ids"] == []

    async def test_status_completed_on_no_flakes(
        self, mock_all_consistent_failures: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await flake_detector(red_phase_state)
        assert result["status"] == "completed"

    async def test_tdd_phase_remains_green(
        self, mock_all_consistent_failures: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await flake_detector(red_phase_state)
        assert result["tdd_phase"] == TDDPhase.GREEN


class TestFlakeDetectorWithFlakes:
    async def test_detects_flaky_test_id(
        self, mock_one_flaky_run: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await flake_detector(red_phase_state)
        assert "test_a" in result["flaky_test_ids"]

    async def test_status_completed_even_with_flakes(
        self, mock_one_flaky_run: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await flake_detector(red_phase_state)
        assert result["status"] == "completed"

    async def test_error_contains_flaky_test_id(
        self, mock_one_flaky_run: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        result = await flake_detector(red_phase_state)
        assert result.get("error") is not None
        assert "test_a" in result["error"]


class TestFlakeDetectorRunCount:
    async def test_runs_exactly_flake_run_count_times(
        self, mock_all_consistent_failures: AsyncMock, red_phase_state: TestAgentState
    ) -> None:
        import test_agent.nodes.flake_detector as mod
        await flake_detector(red_phase_state)
        assert mock_all_consistent_failures.call_count == mod.FLAKE_RUN_COUNT

    async def test_flake_run_count_configurable(
        self, monkeypatch: pytest.MonkeyPatch, red_phase_state: TestAgentState
    ) -> None:
        import test_agent.nodes.flake_detector as mod
        monkeypatch.setattr(mod, "FLAKE_RUN_COUNT", 2)
        mock = AsyncMock(side_effect=[
            _make_run_result(1, ["test_a"]),
            _make_run_result(1, ["test_a"]),
        ])
        monkeypatch.setattr(mod, "_run_pytest", mock)
        await flake_detector(red_phase_state)
        assert mock.call_count == 2
