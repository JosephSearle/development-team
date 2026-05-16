"""Tests for the git_agent node."""

from __future__ import annotations

from unittest.mock import MagicMock

from git_agent.nodes.git_agent import git_agent_node
from git_agent.schema import GitAgentState
from langchain.agents.middleware import SummarizationMiddleware


class TestGitAgentDeepAgentConfig:
    async def test_calls_create_deep_agent(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        await git_agent_node(minimal_git_agent_state)
        mock_deep_agent_git.assert_called_once()

    async def test_github_mcp_tools_wired(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        await git_agent_node(minimal_git_agent_state)
        mock_github_mcp.assert_called_once_with(["github"])
        call_kwargs = mock_deep_agent_git.call_args.kwargs
        assert len(call_kwargs["tools"]) > 0

    async def test_hitl_interrupt_on_create_pull_request(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        await git_agent_node(minimal_git_agent_state)
        call_kwargs = mock_deep_agent_git.call_args.kwargs
        interrupt_on = call_kwargs.get("interrupt_on", {})
        assert interrupt_on.get("create_pull_request") is True

    async def test_no_filesystem_backend(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        await git_agent_node(minimal_git_agent_state)
        call_kwargs = mock_deep_agent_git.call_args.kwargs
        assert "backend" not in call_kwargs or call_kwargs.get("backend") is None

    async def test_langchain_summarization_middleware(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        await git_agent_node(minimal_git_agent_state)
        call_kwargs = mock_deep_agent_git.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_skills_path_set(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        await git_agent_node(minimal_git_agent_state)
        call_kwargs = mock_deep_agent_git.call_args.kwargs
        assert call_kwargs.get("skills") is not None
        assert len(call_kwargs["skills"]) > 0

    async def test_agent_name_is_git_agent(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        await git_agent_node(minimal_git_agent_state)
        call_kwargs = mock_deep_agent_git.call_args.kwargs
        assert call_kwargs.get("name") == "git_agent"


class TestGitAgentResult:
    async def test_returns_messages_from_agent(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        result = await git_agent_node(minimal_git_agent_state)
        assert "messages" in result
        assert len(result["messages"]) > 0  # type: ignore[arg-type]

    async def test_returns_status_completed_on_success(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        result = await git_agent_node(minimal_git_agent_state)
        assert result.get("status") == "completed"
