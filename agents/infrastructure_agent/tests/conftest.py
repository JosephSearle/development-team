"""Shared fixtures for Infrastructure Agent tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from infrastructure_agent.schema import InfrastructureAgentState
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


@pytest.fixture()
def minimal_infra_agent_state() -> InfrastructureAgentState:
    return InfrastructureAgentState(
        subtask_id="sub-001",
        task_description=(
            "Generate a Kubernetes Deployment and Service manifest for the auth service "
            "at image auth-service:1.2.3, 2 replicas, port 8080. "
            "Commit to the GitOps repo at org/gitops-config."
        ),
        manifests=[],
        manifest_paths=[],
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
def mock_github_mcp_infra(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tool = _make_fake_tool("create_or_update_file")
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[fake_tool])
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr(
        "infrastructure_agent.nodes.infrastructure_agent.MCPRegistry.build_client", mock_build
    )
    return mock_build


@pytest.fixture()
def mock_deep_agent_infra(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content="Manifests committed to GitOps repo.")]}
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr(
        "infrastructure_agent.nodes.infrastructure_agent.create_deep_agent", mock_create
    )
    return mock_create
