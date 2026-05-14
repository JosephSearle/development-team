"""Tests for the Architecture Agent LangGraph graph."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from architecture_agent.schema import ArchitectureAgentState


class TestArchitectureAgentGraphStructure:
    def test_graph_builds_without_error(self) -> None:
        from architecture_agent.graph import build_architecture_agent_graph

        graph = build_architecture_agent_graph()
        assert graph is not None

    def test_graph_has_architecture_agent_node(self) -> None:
        from architecture_agent.graph import build_architecture_agent_graph

        graph = build_architecture_agent_graph()
        assert "architecture_agent_node" in graph.nodes

    def test_graph_does_not_have_unexpected_nodes(self) -> None:
        from architecture_agent.graph import build_architecture_agent_graph

        graph = build_architecture_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "output_guardrail" not in node_names
        assert "secrets_scanner" not in node_names
        assert "scan_gate" not in node_names


class TestArchitectureAgentGraphInvocation:
    async def test_graph_invokes_architecture_agent_node(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod
        from architecture_agent.graph import build_architecture_agent_graph

        graph = build_architecture_agent_graph()
        config = {"configurable": {"thread_id": "test-arch-001"}}
        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await graph.ainvoke(minimal_architecture_agent_state, config=config)
        mock_deep_agent_arch.assert_called_once()
        assert result is not None
