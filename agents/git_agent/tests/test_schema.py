"""Tests for GitAgentState schema."""

from __future__ import annotations

from git_agent.schema import GitAgentState
from langchain_core.messages import HumanMessage


class TestGitAgentStateKeys:
    def test_required_keys_present(self) -> None:
        state = GitAgentState(
            subtask_id="sub-001",
            task_description="Create a feature branch and open a PR",
            branch_name="feat/add-login",
            pr_url=None,
            commit_messages=[],
            messages=[],
            status="in_progress",
            error=None,
        )
        assert state["subtask_id"] == "sub-001"
        assert state["task_description"] == "Create a feature branch and open a PR"
        assert state["branch_name"] == "feat/add-login"
        assert state["pr_url"] is None
        assert state["commit_messages"] == []
        assert state["messages"] == []
        assert state["status"] == "in_progress"
        assert state["error"] is None

    def test_pr_url_accepts_string(self) -> None:
        state = GitAgentState(
            subtask_id="sub-002",
            task_description="Open PR",
            branch_name="feat/thing",
            pr_url="https://github.com/org/repo/pull/42",
            commit_messages=["feat: add thing"],
            messages=[],
            status="completed",
            error=None,
        )
        assert state["pr_url"] == "https://github.com/org/repo/pull/42"

    def test_commit_messages_is_list(self) -> None:
        state = GitAgentState(
            subtask_id="sub-003",
            task_description="Commit",
            branch_name="feat/x",
            pr_url=None,
            commit_messages=["feat: first", "fix: second"],
            messages=[],
            status="in_progress",
            error=None,
        )
        assert len(state["commit_messages"]) == 2

    def test_messages_uses_add_messages_reducer(self) -> None:
        msg = HumanMessage(content="hello")
        state = GitAgentState(
            subtask_id="sub-004",
            task_description="Test",
            branch_name="feat/y",
            pr_url=None,
            commit_messages=[],
            messages=[msg],
            status="in_progress",
            error=None,
        )
        assert len(state["messages"]) == 1

    def test_error_accepts_string(self) -> None:
        state = GitAgentState(
            subtask_id="sub-005",
            task_description="Test",
            branch_name="feat/z",
            pr_url=None,
            commit_messages=[],
            messages=[],
            status="failed",
            error="GitHub API rate limited",
        )
        assert state["error"] == "GitHub API rate limited"
