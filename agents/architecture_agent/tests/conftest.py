"""Shared fixtures for Architecture Agent tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from architecture_agent.schema import ArchitectureAgentState
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


@pytest.fixture()
def minimal_architecture_agent_state() -> ArchitectureAgentState:
    return ArchitectureAgentState(
        subtask_id="sub-001",
        task_description=(
            "Evaluate LangGraph vs raw LangChain for orchestration and write an ADR "
            "capturing the decision with trade-offs."
        ),
        workspace="/tmp/dev-team/sub-001",
        decision_rationale="",
        options_evaluated=[],
        adr_path=None,
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
def mock_mcp_arch(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tool = _make_fake_tool("context7_search")
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[fake_tool])
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr(
        "architecture_agent.nodes.architecture_agent.MCPRegistry.build_client", mock_build
    )
    return mock_build


@pytest.fixture()
def mock_deep_agent_arch(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "messages": [AIMessage(content="ADR written: adopting LangGraph for orchestration.")]
        }
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr(
        "architecture_agent.nodes.architecture_agent.create_deep_agent", mock_create
    )
    return mock_create
