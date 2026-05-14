"""Tests for DocsAgentState schema."""

from __future__ import annotations

from docs_agent.schema import DocsAgentState
from langchain_core.messages import HumanMessage


class TestDocsAgentStateKeys:
    def test_required_keys_present(self) -> None:
        state = DocsAgentState(
            subtask_id="sub-001",
            task_description="Write README for auth-service",
            workspace="/tmp/dev-team/sub-001",
            file_paths_updated=[],
            changelog_entry="",
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["subtask_id"] == "sub-001"
        assert "README" in state["task_description"]
        assert state["workspace"] == "/tmp/dev-team/sub-001"
        assert state["file_paths_updated"] == []
        assert state["changelog_entry"] == ""
        assert state["messages"] == []
        assert state["status"] == "in_progress"
        assert state["error"] is None

    def test_file_paths_updated_accepts_list_of_strings(self) -> None:
        state = DocsAgentState(
            subtask_id="sub-002",
            task_description="Update API docs",
            workspace="/tmp/dev-team/sub-002",
            file_paths_updated=[
                "/tmp/dev-team/sub-002/docs/README.md",
                "/tmp/dev-team/sub-002/docs/API.md",
            ],
            changelog_entry="",
            messages=[],
            status="completed",
            error=None,
        )
        assert len(state["file_paths_updated"]) == 2

    def test_changelog_entry_accepts_string(self) -> None:
        entry = "## [1.3.0] — 2026-05-14\n### Added\n- Auth service README\n"
        state = DocsAgentState(
            subtask_id="sub-003",
            task_description="Update changelog",
            workspace="/tmp/dev-team/sub-003",
            file_paths_updated=[],
            changelog_entry=entry,
            messages=[],
            status="completed",
            error=None,
        )
        assert "1.3.0" in state["changelog_entry"]

    def test_messages_uses_add_messages_reducer(self) -> None:
        msg = HumanMessage(content="write the docs")
        state = DocsAgentState(
            subtask_id="sub-004",
            task_description="Test",
            workspace="/tmp/dev-team/sub-004",
            file_paths_updated=[],
            changelog_entry="",
            messages=[msg],
            status="in_progress",
            error=None,
        )
        assert len(state["messages"]) == 1

    def test_error_accepts_string(self) -> None:
        state = DocsAgentState(
            subtask_id="sub-005",
            task_description="Test",
            workspace="/tmp/dev-team/sub-005",
            file_paths_updated=[],
            changelog_entry="",
            messages=[],
            status="failed",
            error="GitHub MCP connection refused",
        )
        assert state["error"] == "GitHub MCP connection refused"
