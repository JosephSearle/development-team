"""Shared fixtures for Git Agent tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from git_agent.schema import GitAgentState
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


@pytest.fixture()
def minimal_git_agent_state() -> GitAgentState:
    return GitAgentState(
        subtask_id="sub-001",
        task_description="Create branch feat/add-login and open a pull request",
        branch_name="feat/add-login",
        pr_url=None,
        commit_messages=[],
        messages=[],
        status="in_progress",
        error=None,
    )


def _make_fake_tool(name: str) -> BaseTool:
    tool = MagicMock(spec=BaseTool)
    tool.name = name
    tool.ainvoke = AsyncMock(return_value="ok")
    return tool


@pytest.fixture()
def mock_github_mcp(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tool = _make_fake_tool("create_pull_request")
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[fake_tool])
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr("git_agent.nodes.git_agent.MCPRegistry.build_client", mock_build)
    return mock_build


@pytest.fixture()
def mock_deep_agent_git(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "messages": [AIMessage(content="PR opened at https://github.com/org/repo/pull/1")],
            "pr_url": "https://github.com/org/repo/pull/1",
        }
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr("git_agent.nodes.git_agent.create_deep_agent", mock_create)
    return mock_create
