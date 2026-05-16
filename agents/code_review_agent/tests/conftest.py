"""Shared fixtures for Code Review Agent tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from code_review_agent.schema import CodeReviewAgentState
from dev_team_state.schema import TDDPhase, TestRunResult
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


@pytest.fixture()
def passing_test_run_result() -> TestRunResult:
    return TestRunResult(
        exit_code=0,
        passed=5,
        failed=0,
        errors=0,
        duration_seconds=2.1,
        coverage_line_pct=91.0,
        coverage_branch_pct=82.0,
        failure_details=[],
        raw_output="5 passed in 2.1s",
    )


@pytest.fixture()
def minimal_review_state(passing_test_run_result: TestRunResult) -> CodeReviewAgentState:
    return CodeReviewAgentState(
        subtask_id="sub-001",
        feature_spec="Implement an add(a, b) function",
        tdd_phase=TDDPhase.GREEN,
        written_code="def add(a: int, b: int) -> int:\n    return a + b\n",
        test_results=passing_test_run_result,
        agent_results=[],
        scan_complete=False,
        review_result=None,
        messages=[],
        status="in_progress",
        error=None,
    )


@pytest.fixture()
def scan_complete_state(minimal_review_state: CodeReviewAgentState) -> CodeReviewAgentState:
    return CodeReviewAgentState(
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
            "scan_complete": True,
        }
    )


_REVIEW_JSON = (
    '{"approved": true, "reviewer_model": "qwen3.5-72b-instruct",'
    ' "comments": ["Looks good"], "blocking_issues": [], "metadata": {}}'
)


def _make_fake_tool(name: str) -> BaseTool:
    tool = MagicMock(spec=BaseTool)
    tool.name = name
    tool.ainvoke = AsyncMock(return_value="ok")
    return tool


@pytest.fixture()
def mock_github_mcp(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tool = _make_fake_tool("get_pull_request")
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[fake_tool])
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr("code_review_agent.nodes.reviewer.MCPRegistry.build_client", mock_build)
    return mock_build


@pytest.fixture()
def mock_deep_agent_reviewer(
    monkeypatch: pytest.MonkeyPatch, mock_github_mcp: MagicMock
) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content=_REVIEW_JSON)]}
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr("code_review_agent.nodes.reviewer.create_deep_agent", mock_create)
    return mock_create
