"""Shared fixtures for Code Agent tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from code_agent.schema import CodeAgentState
from dev_team_state.schema import TDDPhase, TestRunResult
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


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
        failure_details=["tests/test_feature.py::test_add"],
        raw_output="FAILED tests/test_feature.py::test_add",
    )


@pytest.fixture()
def minimal_code_agent_state(failing_test_run_result: TestRunResult) -> CodeAgentState:
    return CodeAgentState(
        subtask_id="sub-001",
        feature_spec="Implement an add(a, b) function",
        tdd_phase=TDDPhase.RED,
        test_file_path="/tmp/dev-team/sub-001/tests/test_feature.py",
        test_results=failing_test_run_result,
        written_code=None,
        implementation_file_path=None,
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
        iteration_count=0,
    )


@pytest.fixture()
def refactor_phase_state(failing_test_run_result: TestRunResult) -> CodeAgentState:
    return CodeAgentState(
        subtask_id="sub-001",
        feature_spec="Implement an add(a, b) function",
        tdd_phase=TDDPhase.REFACTOR,
        test_file_path="/tmp/dev-team/sub-001/tests/test_feature.py",
        test_results=failing_test_run_result,
        written_code="def add(a, b):\n    return a + b\n",
        implementation_file_path="/tmp/dev-team/sub-001/src/implementation.py",
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
        iteration_count=1,
    )


def _make_fake_tool(name: str) -> BaseTool:
    tool = MagicMock(spec=BaseTool)
    tool.name = name
    tool.ainvoke = AsyncMock(return_value="library documentation content")
    return tool


@pytest.fixture()
def mock_context7_mcp(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tool = _make_fake_tool("get-library-docs")
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[fake_tool])
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr("code_agent.nodes.code_agent.MCPRegistry.build_client", mock_build)
    return mock_build


@pytest.fixture()
def mock_deep_agent_code(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content="def add(a, b):\n    return a + b\n")]}
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr("code_agent.nodes.code_agent.create_deep_agent", mock_create)
    return mock_create
