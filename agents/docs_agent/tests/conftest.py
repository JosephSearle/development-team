"""Shared fixtures for Documentation Agent tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from docs_agent.schema import DocsAgentState
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


@pytest.fixture()
def minimal_docs_agent_state() -> DocsAgentState:
    return DocsAgentState(
        subtask_id="sub-001",
        task_description=(
            "Write a README for the auth-service covering quick start, configuration, "
            "and API endpoints. Commit to the repository."
        ),
        workspace="/tmp/dev-team/sub-001",
        file_paths_updated=[],
        changelog_entry="",
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
def mock_github_mcp_docs(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tool = _make_fake_tool("create_or_update_file")
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[fake_tool])
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr(
        "docs_agent.nodes.docs_agent.MCPRegistry.build_client", mock_build
    )
    return mock_build


@pytest.fixture()
def mock_deep_agent_docs(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "messages": [AIMessage(content="README written and committed to repository.")]
        }
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr(
        "docs_agent.nodes.docs_agent.create_deep_agent", mock_create
    )
    return mock_create
