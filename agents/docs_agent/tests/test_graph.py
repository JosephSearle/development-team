"""Tests for the Documentation Agent LangGraph graph."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from docs_agent.schema import DocsAgentState


class TestDocsAgentGraphStructure:
    def test_graph_builds_without_error(self) -> None:
        from docs_agent.graph import build_docs_agent_graph

        graph = build_docs_agent_graph()
        assert graph is not None

    def test_graph_has_docs_agent_node(self) -> None:
        from docs_agent.graph import build_docs_agent_graph

        graph = build_docs_agent_graph()
        assert "docs_agent_node" in graph.nodes

    def test_graph_does_not_have_unexpected_nodes(self) -> None:
        from docs_agent.graph import build_docs_agent_graph

        graph = build_docs_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "output_guardrail" not in node_names
        assert "secrets_scanner" not in node_names


class TestDocsAgentGraphInvocation:
    async def test_graph_invokes_docs_agent_node(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod
        from docs_agent.graph import build_docs_agent_graph

        graph = build_docs_agent_graph()
        config = {"configurable": {"thread_id": "test-docs-001"}}
        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await graph.ainvoke(minimal_docs_agent_state, config=config)
        mock_deep_agent_docs.assert_called_once()
        assert result is not None
