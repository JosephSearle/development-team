"""Tests for the Code Agent graph — kept minimal; node-level tests are in test_code_agent.py."""

from __future__ import annotations

from code_agent.graph import build_code_agent_graph


class TestCodeAgentGraphBuild:
    def test_graph_builds_without_error(self) -> None:
        graph = build_code_agent_graph()
        assert graph is not None

    def test_graph_accepts_checkpointer(self) -> None:
        from langgraph.checkpoint.memory import MemorySaver

        graph = build_code_agent_graph(checkpointer=MemorySaver())
        assert graph is not None
