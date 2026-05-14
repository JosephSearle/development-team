"""Tests for the Code Review Agent graph."""

from __future__ import annotations

from code_review_agent.graph import build_code_review_agent_graph
from code_review_agent.schema import CodeReviewAgentState


class TestCodeReviewAgentGraphBuild:
    def test_graph_builds_without_error(self) -> None:
        graph = build_code_review_agent_graph()
        assert graph is not None

    def test_graph_has_expected_nodes(self) -> None:
        graph = build_code_review_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "scan_gate" in node_names
        assert "reviewer" in node_names

    def test_graph_accepts_checkpointer(self) -> None:
        from langgraph.checkpoint.memory import MemorySaver
        graph = build_code_review_agent_graph(checkpointer=MemorySaver())
        assert graph is not None


class TestCodeReviewAgentGraphRouting:
    async def test_blocked_scan_ends_without_review(
        self,
        minimal_review_state: CodeReviewAgentState,
    ) -> None:
        graph = build_code_review_agent_graph()
        config = {"configurable": {"thread_id": "test-blocked"}}
        result = await graph.ainvoke(minimal_review_state, config=config)
        assert result.get("scan_complete") is False
        assert result.get("review_result") is None

    async def test_completed_scan_proceeds_to_reviewer(
        self,
        mock_deep_agent_reviewer: object,
        scan_complete_state: CodeReviewAgentState,
    ) -> None:
        graph = build_code_review_agent_graph()
        config = {"configurable": {"thread_id": "test-review"}}
        result = await graph.ainvoke(scan_complete_state, config=config)
        assert result.get("review_result") is not None
