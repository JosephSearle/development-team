"""Tests for the Incident Response Agent LangGraph graph."""

from __future__ import annotations

from unittest.mock import MagicMock

from incident_response_agent.schema import IncidentResponseAgentState


class TestIncidentResponseAgentGraphStructure:
    def test_graph_builds_without_error(self) -> None:
        from incident_response_agent.graph import build_incident_response_agent_graph

        graph = build_incident_response_agent_graph()
        assert graph is not None

    def test_graph_has_incident_agent_node(self) -> None:
        from incident_response_agent.graph import build_incident_response_agent_graph

        graph = build_incident_response_agent_graph()
        assert "incident_agent_node" in graph.nodes

    def test_graph_does_not_have_unexpected_nodes(self) -> None:
        from incident_response_agent.graph import build_incident_response_agent_graph

        graph = build_incident_response_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "output_guardrail" not in node_names
        assert "secrets_scanner" not in node_names


class TestIncidentResponseAgentGraphInvocation:
    async def test_graph_invokes_incident_agent_node(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        from incident_response_agent.graph import build_incident_response_agent_graph

        graph = build_incident_response_agent_graph()
        config = {"configurable": {"thread_id": "test-incident-001"}}
        result = await graph.ainvoke(minimal_incident_agent_state, config=config)
        mock_deep_agent_incident.assert_called_once()
        assert result is not None
