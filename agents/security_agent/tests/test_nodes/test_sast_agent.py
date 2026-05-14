"""Tests for the sast_agent node."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from security_agent.nodes.sast_agent import sast_agent_node
from security_agent.schema import SecurityAgentState


def _make_state(secrets_detected: bool = False) -> SecurityAgentState:
    return SecurityAgentState(
        subtask_id="sub-001",
        diff_content="+def add(a, b):\n+    return a + b",
        secrets_detected=secrets_detected,
        scan_complete=False,
        sast_findings=[],
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
    )


def _make_fake_tool(name: str) -> BaseTool:
    tool = MagicMock(spec=BaseTool)
    tool.name = name
    tool.ainvoke = AsyncMock(return_value="scan result")
    return tool


@pytest.fixture()
def mock_sonarqube_github_mcp(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tools = [_make_fake_tool("sonarqube_scan"), _make_fake_tool("create_pull_request")]
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=fake_tools)
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr("security_agent.nodes.sast_agent.MCPRegistry.build_client", mock_build)
    return mock_build


@pytest.fixture()
def mock_deep_agent_sast(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "messages": [AIMessage(content='{"sast_findings": [], "scan_complete": true}')],
        }
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr("security_agent.nodes.sast_agent.create_deep_agent", mock_create)
    return mock_create


class TestSASTAgentShortCircuit:
    async def test_returns_empty_when_secrets_detected(self) -> None:
        state = _make_state(secrets_detected=True)
        result = await sast_agent_node(state)
        assert result == {}

    async def test_proceeds_when_no_secrets(
        self,
        mock_deep_agent_sast: MagicMock,
        mock_sonarqube_github_mcp: MagicMock,
    ) -> None:
        state = _make_state(secrets_detected=False)
        result = await sast_agent_node(state)
        mock_deep_agent_sast.assert_called_once()
        assert result != {}


class TestSASTAgentDeepAgentConfig:
    async def test_sonarqube_and_github_mcp_tools_wired(
        self,
        mock_deep_agent_sast: MagicMock,
        mock_sonarqube_github_mcp: MagicMock,
    ) -> None:
        await sast_agent_node(_make_state())
        mock_sonarqube_github_mcp.assert_called_once_with(["sonarqube", "github"])

    async def test_hitl_interrupt_on_quality_gate(
        self,
        mock_deep_agent_sast: MagicMock,
        mock_sonarqube_github_mcp: MagicMock,
    ) -> None:
        await sast_agent_node(_make_state())
        call_kwargs = mock_deep_agent_sast.call_args.kwargs
        assert call_kwargs.get("interrupt_on", {}).get("sonarqube_set_quality_gate") is True

    async def test_no_filesystem_backend(
        self,
        mock_deep_agent_sast: MagicMock,
        mock_sonarqube_github_mcp: MagicMock,
    ) -> None:
        await sast_agent_node(_make_state())
        call_kwargs = mock_deep_agent_sast.call_args.kwargs
        assert "backend" not in call_kwargs or call_kwargs.get("backend") is None

    async def test_langchain_summarization_middleware(
        self,
        mock_deep_agent_sast: MagicMock,
        mock_sonarqube_github_mcp: MagicMock,
    ) -> None:
        await sast_agent_node(_make_state())
        call_kwargs = mock_deep_agent_sast.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_skills_path_set(
        self,
        mock_deep_agent_sast: MagicMock,
        mock_sonarqube_github_mcp: MagicMock,
    ) -> None:
        await sast_agent_node(_make_state())
        call_kwargs = mock_deep_agent_sast.call_args.kwargs
        assert call_kwargs.get("skills") is not None
        assert len(call_kwargs["skills"]) > 0


class TestSASTAgentResult:
    async def test_returns_scan_complete_true(
        self,
        mock_deep_agent_sast: MagicMock,
        mock_sonarqube_github_mcp: MagicMock,
    ) -> None:
        result = await sast_agent_node(_make_state())
        assert result.get("scan_complete") is True
