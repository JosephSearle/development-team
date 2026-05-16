"""Tests for the CI/CD Agent LangGraph graph."""

from __future__ import annotations

from unittest.mock import MagicMock

from cicd_agent.schema import CICDAgentState


class TestCICDAgentGraphStructure:
    def test_graph_builds_without_error(self) -> None:
        from cicd_agent.graph import build_cicd_agent_graph

        graph = build_cicd_agent_graph()
        assert graph is not None

    def test_graph_has_cicd_agent_node(self) -> None:
        from cicd_agent.graph import build_cicd_agent_graph

        graph = build_cicd_agent_graph()
        assert "cicd_agent_node" in graph.nodes

    def test_graph_does_not_have_unexpected_nodes(self) -> None:
        from cicd_agent.graph import build_cicd_agent_graph

        graph = build_cicd_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "output_guardrail" not in node_names
        assert "secrets_scanner" not in node_names


class TestCICDAgentGraphInvocation:
    async def test_graph_invokes_cicd_agent_node(
        self,
        mock_deep_agent_cicd: MagicMock,
        mock_jenkins_github_mcp: MagicMock,
        minimal_cicd_agent_state: CICDAgentState,
    ) -> None:
        from cicd_agent.graph import build_cicd_agent_graph

        graph = build_cicd_agent_graph()
        config = {"configurable": {"thread_id": "test-cicd-001"}}
        result = await graph.ainvoke(minimal_cicd_agent_state, config=config)
        mock_deep_agent_cicd.assert_called_once()
        assert result is not None
