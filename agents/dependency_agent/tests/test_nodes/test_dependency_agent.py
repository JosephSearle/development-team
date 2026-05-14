"""Tests for the dependency_agent node."""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain.agents.middleware import SummarizationMiddleware
from dependency_agent.nodes.dependency_agent import dependency_agent_node
from dependency_agent.schema import DependencyAgentState


class TestDependencyAgentDeepAgentConfig:
    async def test_calls_create_deep_agent(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        await dependency_agent_node(minimal_dependency_agent_state)
        mock_deep_agent_dependency.assert_called_once()

    async def test_github_and_sonarqube_mcp_tools_wired(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        await dependency_agent_node(minimal_dependency_agent_state)
        mock_mcp_dependency.assert_called_once_with(["github", "sonarqube"])

    async def test_no_filesystem_backend(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        await dependency_agent_node(minimal_dependency_agent_state)
        call_kwargs = mock_deep_agent_dependency.call_args.kwargs
        assert call_kwargs.get("backend") is None

    async def test_langchain_summarization_middleware(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        await dependency_agent_node(minimal_dependency_agent_state)
        call_kwargs = mock_deep_agent_dependency.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_no_subagents(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        await dependency_agent_node(minimal_dependency_agent_state)
        call_kwargs = mock_deep_agent_dependency.call_args.kwargs
        assert call_kwargs.get("subagents") is None

    async def test_no_interrupt_on(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        await dependency_agent_node(minimal_dependency_agent_state)
        call_kwargs = mock_deep_agent_dependency.call_args.kwargs
        assert call_kwargs.get("interrupt_on") is None

    async def test_skills_path_set(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        await dependency_agent_node(minimal_dependency_agent_state)
        call_kwargs = mock_deep_agent_dependency.call_args.kwargs
        assert call_kwargs.get("skills") is not None
        assert len(call_kwargs["skills"]) > 0

    async def test_agent_name_is_dependency_agent(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        await dependency_agent_node(minimal_dependency_agent_state)
        call_kwargs = mock_deep_agent_dependency.call_args.kwargs
        assert call_kwargs.get("name") == "dependency_agent"


class TestDependencyAgentPRUrlExtraction:
    async def test_extracts_pr_url_from_ai_message(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        result = await dependency_agent_node(minimal_dependency_agent_state)
        assert result.get("pr_urls") is not None
        assert len(result["pr_urls"]) == 1  # type: ignore[arg-type]
        assert result["pr_urls"][0] == "https://github.com/org/repo/pull/42"  # type: ignore[index]

    async def test_returns_empty_pr_urls_when_none_opened(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
        monkeypatch: object,
    ) -> None:
        from unittest.mock import AsyncMock
        from langchain_core.messages import AIMessage

        mock_deep_agent_dependency.return_value.ainvoke = AsyncMock(
            return_value={"messages": [AIMessage(content="No vulnerabilities found.")]}
        )
        result = await dependency_agent_node(minimal_dependency_agent_state)
        assert result.get("pr_urls") == []

    async def test_returns_status_completed(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        result = await dependency_agent_node(minimal_dependency_agent_state)
        assert result.get("status") == "completed"
