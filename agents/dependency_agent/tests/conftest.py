"""Shared fixtures for Dependency Agent tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from dependency_agent.schema import DependencyAgentState
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


@pytest.fixture()
def minimal_dependency_agent_state() -> DependencyAgentState:
    return DependencyAgentState(
        subtask_id="sub-001",
        task_description=(
            "Scan the repository for outdated dependencies and known CVEs. "
            "Open PRs for Critical and High severity vulnerabilities."
        ),
        dependencies_scanned=[],
        vulnerabilities_found=[],
        upgrades_proposed=[],
        pr_urls=[],
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
def mock_mcp_dependency(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tool = _make_fake_tool("search_issues")
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[fake_tool])
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr(
        "dependency_agent.nodes.dependency_agent.MCPRegistry.build_client", mock_build
    )
    return mock_build


@pytest.fixture()
def mock_deep_agent_dependency(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "messages": [
                AIMessage(
                    content=(
                        "Opened upgrade PR: "
                        "https://github.com/org/repo/pull/42 "
                        "for CVE-2026-1234 in requests 2.28.0."
                    )
                )
            ]
        }
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr(
        "dependency_agent.nodes.dependency_agent.create_deep_agent", mock_create
    )
    return mock_create
