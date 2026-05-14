"""Shared fixtures for CI/CD Agent tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from cicd_agent.schema import CICDAgentState
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


@pytest.fixture()
def minimal_cicd_agent_state() -> CICDAgentState:
    return CICDAgentState(
        subtask_id="sub-001",
        task_description="Trigger a Jenkins build for the feature branch and monitor status",
        pipeline_type="jenkins",
        build_url=None,
        deployment_env="staging",
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
def mock_jenkins_github_mcp(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tools = [
        _make_fake_tool("trigger_build"),
        _make_fake_tool("trigger_production_deploy"),
        _make_fake_tool("create_pull_request"),
    ]
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=fake_tools)
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr("cicd_agent.nodes.cicd_agent.MCPRegistry.build_client", mock_build)
    return mock_build


@pytest.fixture()
def mock_deep_agent_cicd(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "messages": [
                AIMessage(content="Build triggered at https://jenkins.example.com/build/42")
            ],
        }
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr("cicd_agent.nodes.cicd_agent.create_deep_agent", mock_create)
    return mock_create
