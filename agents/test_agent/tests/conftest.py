"""Shared fixtures for Test Agent tests."""

from __future__ import annotations

import pytest
from dev_team_state.schema import TDDPhase, TestRunResult
from test_agent.schema import TestAgentState


@pytest.fixture()
def failing_test_run_result() -> TestRunResult:
    return TestRunResult(
        exit_code=1,
        passed=0,
        failed=3,
        errors=0,
        duration_seconds=1.2,
        coverage_line_pct=None,
        coverage_branch_pct=None,
        failure_details=[
            "tests/test_feature.py::test_add",
            "tests/test_feature.py::test_subtract",
        ],
        raw_output=(
            "FAILED tests/test_feature.py::test_add\n"
            "FAILED tests/test_feature.py::test_subtract"
        ),
    )


@pytest.fixture()
def passing_test_run_result() -> TestRunResult:
    return TestRunResult(
        exit_code=0,
        passed=5,
        failed=0,
        errors=0,
        duration_seconds=0.8,
        coverage_line_pct=85.0,
        coverage_branch_pct=72.0,
        failure_details=[],
        raw_output="5 passed in 0.8s",
    )


@pytest.fixture()
def minimal_test_agent_state() -> TestAgentState:
    return TestAgentState(
        subtask_id="sub-001",
        feature_spec="Implement an add(a, b) function that returns the sum of two integers",
        tdd_phase=TDDPhase.SETUP,
        test_file_path=None,
        test_code=None,
        test_results=None,
        run_count=0,
        flaky_test_ids=[],
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
    )


@pytest.fixture()
def red_phase_state(failing_test_run_result: TestRunResult) -> TestAgentState:
    return TestAgentState(
        subtask_id="sub-001",
        feature_spec="Implement an add(a, b) function that returns the sum of two integers",
        tdd_phase=TDDPhase.RED,
        test_file_path="/tmp/dev-team/sub-001/tests/test_feature.py",
        test_code="import pytest\n\ndef test_add():\n    assert False",
        test_results=failing_test_run_result,
        run_count=1,
        flaky_test_ids=[],
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
    )
