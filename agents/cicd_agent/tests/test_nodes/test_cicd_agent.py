"""Tests for the cicd_agent node."""

from __future__ import annotations

from unittest.mock import MagicMock

from cicd_agent.nodes.cicd_agent import cicd_agent_node
from cicd_agent.schema import CICDAgentState
from langchain.agents.middleware import SummarizationMiddleware


class TestCICDAgentDeepAgentConfig:
    async def test_calls_create_deep_agent(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        await cicd_agent_node(minimal_cicd_agent_state)
        mock_deep_agent_cicd.assert_called_once()

    async def test_jenkins_and_github_mcp_tools_wired(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        await cicd_agent_node(minimal_cicd_agent_state)
        mock_jenkins_github_mcp.assert_called_once_with(["jenkins", "github"])
        call_kwargs = mock_deep_agent_cicd.call_args.kwargs
        assert len(call_kwargs["tools"]) > 0

    async def test_hitl_interrupt_on_production_deploy(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        await cicd_agent_node(minimal_cicd_agent_state)
        call_kwargs = mock_deep_agent_cicd.call_args.kwargs
        assert call_kwargs.get("interrupt_on", {}).get("trigger_production_deploy") is True

    async def test_no_filesystem_backend(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        await cicd_agent_node(minimal_cicd_agent_state)
        call_kwargs = mock_deep_agent_cicd.call_args.kwargs
        assert "backend" not in call_kwargs or call_kwargs.get("backend") is None

    async def test_langchain_summarization_middleware(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        await cicd_agent_node(minimal_cicd_agent_state)
        call_kwargs = mock_deep_agent_cicd.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_skills_path_set(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        await cicd_agent_node(minimal_cicd_agent_state)
        call_kwargs = mock_deep_agent_cicd.call_args.kwargs
        assert call_kwargs.get("skills") is not None
        assert len(call_kwargs["skills"]) > 0

    async def test_agent_name_is_cicd_agent(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        await cicd_agent_node(minimal_cicd_agent_state)
        call_kwargs = mock_deep_agent_cicd.call_args.kwargs
        assert call_kwargs.get("name") == "cicd_agent"


class TestCICDAgentResult:
    async def test_returns_messages_from_agent(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        result = await cicd_agent_node(minimal_cicd_agent_state)
        assert "messages" in result
        assert len(result["messages"]) > 0  # type: ignore[arg-type]

    async def test_returns_status_completed(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        result = await cicd_agent_node(minimal_cicd_agent_state)
        assert result.get("status") == "completed"
