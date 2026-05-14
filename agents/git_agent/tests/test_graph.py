"""Tests for the Git Agent LangGraph graph."""

from __future__ import annotations

from unittest.mock import MagicMock

from git_agent.schema import GitAgentState


class TestGitAgentGraphStructure:
    def test_graph_builds_without_error(self) -> None:
        from git_agent.graph import build_git_agent_graph

        graph = build_git_agent_graph()
        assert graph is not None

    def test_graph_has_git_agent_node(self) -> None:
        from git_agent.graph import build_git_agent_graph

        graph = build_git_agent_graph()
        assert "git_agent_node" in graph.nodes

    def test_graph_does_not_have_unexpected_nodes(self) -> None:
        from git_agent.graph import build_git_agent_graph

        graph = build_git_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "code_agent_node" not in node_names
        assert "output_guardrail" not in node_names


class TestGitAgentGraphInvocation:
    async def test_graph_invokes_git_agent_node(
        self,
        mock_deep_agent_git: MagicMock,
        mock_github_mcp: MagicMock,
        minimal_git_agent_state: GitAgentState,
    ) -> None:
        from git_agent.graph import build_git_agent_graph

        graph = build_git_agent_graph()
        config = {"configurable": {"thread_id": "test-git-001"}}
        result = await graph.ainvoke(minimal_git_agent_state, config=config)
        mock_deep_agent_git.assert_called_once()
        assert result is not None
