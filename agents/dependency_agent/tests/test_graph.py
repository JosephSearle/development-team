"""Tests for the Dependency Agent LangGraph graph."""

from __future__ import annotations

from unittest.mock import MagicMock

from dependency_agent.schema import DependencyAgentState


class TestDependencyAgentGraphStructure:
    def test_graph_builds_without_error(self) -> None:
        from dependency_agent.graph import build_dependency_agent_graph

        graph = build_dependency_agent_graph()
        assert graph is not None

    def test_graph_has_dependency_agent_node(self) -> None:
        from dependency_agent.graph import build_dependency_agent_graph

        graph = build_dependency_agent_graph()
        assert "dependency_agent_node" in graph.nodes

    def test_graph_does_not_have_unexpected_nodes(self) -> None:
        from dependency_agent.graph import build_dependency_agent_graph

        graph = build_dependency_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "output_guardrail" not in node_names
        assert "secrets_scanner" not in node_names


class TestDependencyAgentGraphInvocation:
    async def test_graph_invokes_dependency_agent_node(
        self,
        mock_deep_agent_dependency: MagicMock,
        mock_mcp_dependency: MagicMock,
        minimal_dependency_agent_state: DependencyAgentState,
    ) -> None:
        from dependency_agent.graph import build_dependency_agent_graph

        graph = build_dependency_agent_graph()
        config = {"configurable": {"thread_id": "test-dep-001"}}
        result = await graph.ainvoke(minimal_dependency_agent_state, config=config)
        mock_deep_agent_dependency.assert_called_once()
        assert result is not None
