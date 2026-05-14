"""Tests for InfrastructureAgentState schema."""

from __future__ import annotations

from infrastructure_agent.schema import InfrastructureAgentState
from langchain_core.messages import HumanMessage


class TestInfrastructureAgentStateKeys:
    def test_required_keys_present(self) -> None:
        state = InfrastructureAgentState(
            subtask_id="sub-001",
            task_description="Generate a Kubernetes deployment manifest for the auth service",
            manifests=[],
            manifest_paths=[],
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["subtask_id"] == "sub-001"
        assert "Kubernetes" in state["task_description"]
        assert state["manifests"] == []
        assert state["manifest_paths"] == []
        assert state["messages"] == []
        assert state["status"] == "in_progress"
        assert state["error"] is None

    def test_manifests_accepts_list_of_strings(self) -> None:
        manifest_yaml = "apiVersion: apps/v1\nkind: Deployment\n"
        state = InfrastructureAgentState(
            subtask_id="sub-002",
            task_description="Deploy auth service",
            manifests=[manifest_yaml],
            manifest_paths=["/workspace/manifests/deployment.yaml"],
            messages=[],
            status="in_progress",
            error=None,
        )
        assert len(state["manifests"]) == 1
        assert "apiVersion" in state["manifests"][0]

    def test_manifest_paths_accepts_list_of_strings(self) -> None:
        state = InfrastructureAgentState(
            subtask_id="sub-003",
            task_description="Deploy",
            manifests=["content1", "content2"],
            manifest_paths=["/workspace/manifests/deploy.yaml", "/workspace/manifests/svc.yaml"],
            messages=[],
            status="in_progress",
            error=None,
        )
        assert len(state["manifest_paths"]) == 2

    def test_messages_uses_add_messages_reducer(self) -> None:
        msg = HumanMessage(content="generate k8s manifest")
        state = InfrastructureAgentState(
            subtask_id="sub-004",
            task_description="Test",
            manifests=[],
            manifest_paths=[],
            messages=[msg],
            status="in_progress",
            error=None,
        )
        assert len(state["messages"]) == 1

    def test_error_accepts_string(self) -> None:
        state = InfrastructureAgentState(
            subtask_id="sub-005",
            task_description="Test",
            manifests=[],
            manifest_paths=[],
            messages=[],
            status="failed",
            error="Invalid manifest syntax",
        )
        assert state["error"] == "Invalid manifest syntax"
