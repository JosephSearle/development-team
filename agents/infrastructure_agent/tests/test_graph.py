"""Tests for the Infrastructure Agent LangGraph graph."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from infrastructure_agent.schema import InfrastructureAgentState


class TestInfrastructureAgentGraphStructure:
    def test_graph_builds_without_error(self) -> None:
        from infrastructure_agent.graph import build_infrastructure_agent_graph

        graph = build_infrastructure_agent_graph()
        assert graph is not None

    def test_graph_has_infrastructure_agent_node(self) -> None:
        from infrastructure_agent.graph import build_infrastructure_agent_graph

        graph = build_infrastructure_agent_graph()
        assert "infrastructure_agent_node" in graph.nodes

    def test_graph_does_not_have_unexpected_nodes(self) -> None:
        from infrastructure_agent.graph import build_infrastructure_agent_graph

        graph = build_infrastructure_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "output_guardrail" not in node_names
        assert "secrets_scanner" not in node_names


class TestInfrastructureAgentGraphInvocation:
    async def test_graph_invokes_infrastructure_agent_node(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod
        from infrastructure_agent.graph import build_infrastructure_agent_graph

        graph = build_infrastructure_agent_graph()
        config = {"configurable": {"thread_id": "test-infra-001"}}
        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await graph.ainvoke(minimal_infra_agent_state, config=config)
        mock_deep_agent_infra.assert_called_once()
        assert result is not None
