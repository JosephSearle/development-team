"""Tests for the Security Agent LangGraph graph."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.tools import BaseTool
from security_agent.schema import SecurityAgentState


def _base_state(secrets_detected: bool = False) -> SecurityAgentState:
    return SecurityAgentState(
        subtask_id="sub-001",
        diff_content="+def add(a, b):\n+    return a + b",
        secrets_detected=secrets_detected,
        scan_complete=False,
        sast_findings=[],
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
    )


@pytest.fixture()
def mock_sonarqube_github_mcp(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    tool = MagicMock(spec=BaseTool)
    tool.name = "sonarqube_scan"
    tool.ainvoke = AsyncMock(return_value="ok")
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[tool])
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr("security_agent.nodes.sast_agent.MCPRegistry.build_client", mock_build)
    return mock_build


@pytest.fixture()
def mock_deep_agent_sast(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    from langchain_core.messages import AIMessage

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={"messages": [AIMessage(content="scan complete")]}
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr("security_agent.nodes.sast_agent.create_deep_agent", mock_create)
    return mock_create


@pytest.fixture()
def mock_guardrail(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_result = MagicMock()
    mock_result.passed = True
    mock_client = MagicMock()
    mock_client.screen = AsyncMock(return_value=mock_result)
    mock_cls = MagicMock(return_value=mock_client)
    monkeypatch.setattr("security_agent.nodes.output_guardrail.GuardrailClient", mock_cls)
    return mock_cls


class TestSecurityAgentGraphStructure:
    def test_graph_builds_without_error(self) -> None:
        from security_agent.graph import build_security_agent_graph

        graph = build_security_agent_graph()
        assert graph is not None

    def test_graph_has_required_nodes(self) -> None:
        from security_agent.graph import build_security_agent_graph

        graph = build_security_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "secrets_scanner" in node_names
        assert "sast_agent_node" in node_names
        assert "output_guardrail" in node_names


class TestSecurityAgentGraphRouting:
    async def test_secrets_detected_short_circuits_to_end(
        self,
        mock_deep_agent_sast: MagicMock,
        mock_sonarqube_github_mcp: MagicMock,
        mock_guardrail: MagicMock,
    ) -> None:
        from security_agent.graph import build_security_agent_graph

        state = SecurityAgentState(
            subtask_id="sub-002",
            diff_content="+AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE",
            secrets_detected=False,
            scan_complete=False,
            sast_findings=[],
            guardrail_passed=True,
            messages=[],
            status="in_progress",
            error=None,
        )
        graph = build_security_agent_graph()
        config = {"configurable": {"thread_id": "test-secrets"}}
        result = await graph.ainvoke(state, config=config)
        mock_deep_agent_sast.assert_not_called()
        assert result["secrets_detected"] is True
        assert result["status"] == "failed"

    async def test_clean_diff_reaches_sast_agent(
        self,
        mock_deep_agent_sast: MagicMock,
        mock_sonarqube_github_mcp: MagicMock,
        mock_guardrail: MagicMock,
    ) -> None:
        from security_agent.graph import build_security_agent_graph

        graph = build_security_agent_graph()
        config = {"configurable": {"thread_id": "test-clean"}}
        await graph.ainvoke(_base_state(), config=config)
        mock_deep_agent_sast.assert_called_once()
