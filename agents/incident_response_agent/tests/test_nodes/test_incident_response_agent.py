"""Tests for the incident_response_agent node."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from incident_response_agent.nodes.incident_response_agent import incident_response_agent_node
from incident_response_agent.schema import IncidentResponseAgentState
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import AIMessage


class TestIncidentResponseAgentDeepAgentConfig:
    async def test_calls_create_deep_agent(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        await incident_response_agent_node(minimal_incident_agent_state)
        mock_deep_agent_incident.assert_called_once()

    async def test_github_jira_kubernetes_mcp_tools_wired(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        await incident_response_agent_node(minimal_incident_agent_state)
        mock_mcp_incident.assert_called_once_with(["github", "jira", "kubernetes"])

    async def test_no_filesystem_backend(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        await incident_response_agent_node(minimal_incident_agent_state)
        call_kwargs = mock_deep_agent_incident.call_args.kwargs
        assert call_kwargs.get("backend") is None

    async def test_langchain_summarization_middleware(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        await incident_response_agent_node(minimal_incident_agent_state)
        call_kwargs = mock_deep_agent_incident.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_two_subagents_wired(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        await incident_response_agent_node(minimal_incident_agent_state)
        call_kwargs = mock_deep_agent_incident.call_args.kwargs
        subagents = call_kwargs.get("subagents", [])
        assert len(subagents) == 2
        names = {s["name"] for s in subagents}
        assert names == {"log_analyzer", "metrics_analyzer"}

    async def test_interrupt_on_create_jira_issue(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        await incident_response_agent_node(minimal_incident_agent_state)
        call_kwargs = mock_deep_agent_incident.call_args.kwargs
        assert call_kwargs.get("interrupt_on") == {"create_jira_issue": True}

    async def test_skills_path_set(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        await incident_response_agent_node(minimal_incident_agent_state)
        call_kwargs = mock_deep_agent_incident.call_args.kwargs
        assert call_kwargs.get("skills") is not None
        assert len(call_kwargs["skills"]) > 0

    async def test_agent_name_is_incident_response_agent(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        await incident_response_agent_node(minimal_incident_agent_state)
        call_kwargs = mock_deep_agent_incident.call_args.kwargs
        assert call_kwargs.get("name") == "incident_response_agent"


class TestIncidentResponseAgentOutputExtraction:
    async def test_extracts_jira_url_from_ai_message(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        result = await incident_response_agent_node(minimal_incident_agent_state)
        assert result.get("jira_issue_url") == "https://jira.internal/browse/INC-123"

    async def test_returns_none_jira_url_when_not_found(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        mock_deep_agent_incident.return_value.ainvoke = AsyncMock(
            return_value={
                "messages": [AIMessage(content="Root cause identified: OOMKilled. Awaiting approval.")]  # noqa: E501
            }
        )
        result = await incident_response_agent_node(minimal_incident_agent_state)
        assert result.get("jira_issue_url") is None

    async def test_returns_status_completed(
        self,
        mock_deep_agent_incident: MagicMock,
        mock_mcp_incident: MagicMock,
        minimal_incident_agent_state: IncidentResponseAgentState,
    ) -> None:
        result = await incident_response_agent_node(minimal_incident_agent_state)
        assert result.get("status") == "completed"
