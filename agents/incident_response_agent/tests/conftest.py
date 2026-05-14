"""Shared fixtures for Incident Response Agent tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from incident_response_agent.schema import IncidentResponseAgentState
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool


@pytest.fixture()
def minimal_incident_agent_state() -> IncidentResponseAgentState:
    return IncidentResponseAgentState(
        subtask_id="sub-001",
        task_description=(
            "Auth service is returning 503 errors for 15% of requests. "
            "Diagnose the root cause and propose remediation."
        ),
        alert_context="PagerDuty alert: auth-service HTTP 503 rate >10% for 5 minutes",
        root_cause="",
        remediation_steps=[],
        jira_issue_url=None,
        runbook_path=None,
        messages=[],
        status="in_progress",
        error=None,
    )


def _make_fake_tool(name: str) -> BaseTool:
    tool = MagicMock(spec=BaseTool)
    tool.name = name
    tool.ainvoke = AsyncMock(return_value="ok")
    return tool


@pytest.fixture()
def mock_mcp_incident(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_tool = _make_fake_tool("get_pod_logs")
    mock_client = MagicMock()
    mock_client.get_tools = AsyncMock(return_value=[fake_tool])
    mock_build = MagicMock(return_value=mock_client)
    monkeypatch.setattr(
        "incident_response_agent.nodes.incident_response_agent.MCPRegistry.build_client",
        mock_build,
    )
    return mock_build


@pytest.fixture()
def mock_deep_agent_incident(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(
        return_value={
            "messages": [
                AIMessage(
                    content=(
                        "Root cause: auth-service OOMKilled due to memory leak in session cache. "
                        "Remediation: restart pods and increase memory limit. "
                        "Jira incident created: https://jira.internal/browse/INC-123"
                    )
                )
            ]
        }
    )
    mock_create = MagicMock(return_value=mock_graph)
    monkeypatch.setattr(
        "incident_response_agent.nodes.incident_response_agent.create_deep_agent", mock_create
    )
    return mock_create
