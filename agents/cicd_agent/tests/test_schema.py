"""Tests for CICDAgentState schema."""

from __future__ import annotations

from cicd_agent.schema import CICDAgentState
from langchain_core.messages import HumanMessage


class TestCICDAgentStateKeys:
    def test_required_keys_present(self) -> None:
        state = CICDAgentState(
            subtask_id="sub-001",
            task_description="Trigger a Jenkins build for the main branch",
            pipeline_type=None,
            build_url=None,
            deployment_env=None,
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["subtask_id"] == "sub-001"
        assert state["task_description"] == "Trigger a Jenkins build for the main branch"
        assert state["pipeline_type"] is None
        assert state["build_url"] is None
        assert state["deployment_env"] is None
        assert state["messages"] == []
        assert state["status"] == "in_progress"
        assert state["error"] is None

    def test_pipeline_type_accepts_string(self) -> None:
        state = CICDAgentState(
            subtask_id="sub-002",
            task_description="Trigger build",
            pipeline_type="jenkins",
            build_url=None,
            deployment_env=None,
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["pipeline_type"] == "jenkins"

    def test_build_url_accepts_string(self) -> None:
        state = CICDAgentState(
            subtask_id="sub-003",
            task_description="Monitor build",
            pipeline_type="github_actions",
            build_url="https://github.com/org/repo/actions/runs/12345",
            deployment_env=None,
            messages=[],
            status="in_progress",
            error=None,
        )
        assert "actions/runs" in (state["build_url"] or "")

    def test_deployment_env_accepts_string(self) -> None:
        state = CICDAgentState(
            subtask_id="sub-004",
            task_description="Deploy to production",
            pipeline_type="jenkins",
            build_url=None,
            deployment_env="production",
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["deployment_env"] == "production"

    def test_messages_uses_add_messages_reducer(self) -> None:
        msg = HumanMessage(content="trigger build")
        state = CICDAgentState(
            subtask_id="sub-005",
            task_description="Test",
            pipeline_type=None,
            build_url=None,
            deployment_env=None,
            messages=[msg],
            status="in_progress",
            error=None,
        )
        assert len(state["messages"]) == 1
