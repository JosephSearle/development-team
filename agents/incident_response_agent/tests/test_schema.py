"""Tests for IncidentResponseAgentState schema."""

from __future__ import annotations

from incident_response_agent.schema import IncidentResponseAgentState
from langchain_core.messages import HumanMessage


class TestIncidentResponseAgentStateKeys:
    def test_required_keys_present(self) -> None:
        state = IncidentResponseAgentState(
            subtask_id="sub-001",
            task_description="Auth service returning 503 errors",
            alert_context="PagerDuty: auth-service 503 rate >10%",
            root_cause="",
            remediation_steps=[],
            jira_issue_url=None,
            runbook_path=None,
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["subtask_id"] == "sub-001"
        assert "503" in state["task_description"]
        assert "PagerDuty" in state["alert_context"]
        assert state["root_cause"] == ""
        assert state["remediation_steps"] == []
        assert state["jira_issue_url"] is None
        assert state["runbook_path"] is None
        assert state["messages"] == []
        assert state["status"] == "in_progress"
        assert state["error"] is None

    def test_remediation_steps_accepts_list_of_strings(self) -> None:
        state = IncidentResponseAgentState(
            subtask_id="sub-002",
            task_description="Database connection pool exhausted",
            alert_context="High DB connection wait time",
            root_cause="Connection pool leak in auth-service v1.2.3",
            remediation_steps=[
                "Restart auth-service pods",
                "Increase connection pool limit from 10 to 50",
                "Deploy hotfix v1.2.4",
            ],
            jira_issue_url="https://jira.internal/browse/INC-456",
            runbook_path=None,
            messages=[],
            status="completed",
            error=None,
        )
        assert len(state["remediation_steps"]) == 3

    def test_jira_issue_url_accepts_string(self) -> None:
        url = "https://jira.internal/browse/INC-999"
        state = IncidentResponseAgentState(
            subtask_id="sub-003",
            task_description="Test",
            alert_context="Test alert",
            root_cause="Memory leak",
            remediation_steps=[],
            jira_issue_url=url,
            runbook_path=None,
            messages=[],
            status="completed",
            error=None,
        )
        assert state["jira_issue_url"] == url

    def test_messages_uses_add_messages_reducer(self) -> None:
        msg = HumanMessage(content="diagnose the incident")
        state = IncidentResponseAgentState(
            subtask_id="sub-004",
            task_description="Test",
            alert_context="Test",
            root_cause="",
            remediation_steps=[],
            jira_issue_url=None,
            runbook_path=None,
            messages=[msg],
            status="in_progress",
            error=None,
        )
        assert len(state["messages"]) == 1

    def test_error_accepts_string(self) -> None:
        state = IncidentResponseAgentState(
            subtask_id="sub-005",
            task_description="Test",
            alert_context="Test",
            root_cause="",
            remediation_steps=[],
            jira_issue_url=None,
            runbook_path=None,
            messages=[],
            status="failed",
            error="Kubernetes MCP read timeout",
        )
        assert state["error"] == "Kubernetes MCP read timeout"
