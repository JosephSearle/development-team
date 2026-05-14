"""Tests for DependencyAgentState schema."""

from __future__ import annotations

from dependency_agent.schema import DependencyAgentState
from langchain_core.messages import HumanMessage


class TestDependencyAgentStateKeys:
    def test_required_keys_present(self) -> None:
        state = DependencyAgentState(
            subtask_id="sub-001",
            task_description="Scan for CVEs and propose upgrades",
            dependencies_scanned=[],
            vulnerabilities_found=[],
            upgrades_proposed=[],
            pr_urls=[],
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["subtask_id"] == "sub-001"
        assert "CVE" in state["task_description"]
        assert state["dependencies_scanned"] == []
        assert state["vulnerabilities_found"] == []
        assert state["upgrades_proposed"] == []
        assert state["pr_urls"] == []
        assert state["messages"] == []
        assert state["status"] == "in_progress"
        assert state["error"] is None

    def test_dependencies_scanned_accepts_list_of_strings(self) -> None:
        state = DependencyAgentState(
            subtask_id="sub-002",
            task_description="Test",
            dependencies_scanned=["requests==2.28.0", "fastapi==0.100.0"],
            vulnerabilities_found=[],
            upgrades_proposed=[],
            pr_urls=[],
            messages=[],
            status="in_progress",
            error=None,
        )
        assert len(state["dependencies_scanned"]) == 2

    def test_pr_urls_accepts_list_of_strings(self) -> None:
        state = DependencyAgentState(
            subtask_id="sub-003",
            task_description="Test",
            dependencies_scanned=[],
            vulnerabilities_found=["CVE-2026-1234 in requests 2.28.0 (CVSS 9.1)"],
            upgrades_proposed=["requests 2.28.0 → 2.32.3"],
            pr_urls=["https://github.com/org/repo/pull/42"],
            messages=[],
            status="completed",
            error=None,
        )
        assert len(state["pr_urls"]) == 1
        assert "pull/42" in state["pr_urls"][0]

    def test_messages_uses_add_messages_reducer(self) -> None:
        msg = HumanMessage(content="scan dependencies")
        state = DependencyAgentState(
            subtask_id="sub-004",
            task_description="Test",
            dependencies_scanned=[],
            vulnerabilities_found=[],
            upgrades_proposed=[],
            pr_urls=[],
            messages=[msg],
            status="in_progress",
            error=None,
        )
        assert len(state["messages"]) == 1

    def test_error_accepts_string(self) -> None:
        state = DependencyAgentState(
            subtask_id="sub-005",
            task_description="Test",
            dependencies_scanned=[],
            vulnerabilities_found=[],
            upgrades_proposed=[],
            pr_urls=[],
            messages=[],
            status="failed",
            error="SonarQube connection timeout",
        )
        assert state["error"] == "SonarQube connection timeout"
