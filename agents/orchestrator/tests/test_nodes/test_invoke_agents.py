"""Unit tests for orchestrator invoke_agents node functions."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import orchestrator.nodes.invoke_agents as invoke_mod
import pytest
from dev_team_state import OrchestratorState, TaskStatus
from dev_team_state.schema import AgentResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    *,
    subtask_id: str = "sub-001",
    agent_type: str = "test_agent",
    agent_results: list[AgentResult] | None = None,
    branch_name: str = "feat/test",
    pr_url: str | None = None,
) -> OrchestratorState:
    subtask = {
        "subtask_id": subtask_id,
        "description": "Do something useful",
        "agent_type": agent_type,
        "requires_approval": False,
        "status": "planning",
    }
    return OrchestratorState(
        task_id="task-001",
        task_description="Implement feature",
        plan=[subtask],
        current_subtask=subtask,
        agent_results=agent_results or [],
        human_approvals=[],
        run_id="run-001",
        branch_name=branch_name,
        pr_url=pr_url,
        status=TaskStatus.IN_PROGRESS,
        messages=[],
        guardrail_passed=True,
    )


def _graph_mock(terminal_state: dict[str, Any]) -> MagicMock:
    graph = MagicMock()
    graph.ainvoke = AsyncMock(return_value=terminal_state)
    return MagicMock(return_value=graph)


# ---------------------------------------------------------------------------
# Helper function unit tests
# ---------------------------------------------------------------------------


class TestMarkCompleted:
    def test_marks_matching_subtask(self) -> None:
        plan = [
            {"subtask_id": "sub-001", "status": "planning"},
            {"subtask_id": "sub-002", "status": "planning"},
        ]
        result = invoke_mod._mark_completed(plan, "sub-001")
        assert result[0]["status"] == "completed"
        assert result[1]["status"] == "planning"

    def test_does_not_mutate_original(self) -> None:
        plan = [{"subtask_id": "sub-001", "status": "planning"}]
        invoke_mod._mark_completed(plan, "sub-001")
        assert plan[0]["status"] == "planning"

    def test_no_match_leaves_plan_unchanged(self) -> None:
        plan = [{"subtask_id": "sub-001", "status": "planning"}]
        result = invoke_mod._mark_completed(plan, "sub-999")
        assert result[0]["status"] == "planning"


class TestFindPriorMetadata:
    def test_returns_value_from_matching_agent(self) -> None:
        state = _make_state(
            agent_results=[
                AgentResult(
                    agent_id="test_agent",
                    subtask_id="sub-001",
                    status="completed",
                    output="",
                    metadata={"test_file_path": "/workspace/test.py"},
                )
            ]
        )
        result = invoke_mod._find_prior_metadata(state, "test_agent", "test_file_path")
        assert result == "/workspace/test.py"

    def test_returns_none_when_no_matching_agent(self) -> None:
        state = _make_state()
        result = invoke_mod._find_prior_metadata(state, "test_agent", "test_file_path")
        assert result is None

    def test_returns_most_recent_result(self) -> None:
        state = _make_state(
            agent_results=[
                AgentResult(
                    agent_id="test_agent",
                    subtask_id="sub-001",
                    status="completed",
                    output="",
                    metadata={"test_file_path": "/old/path.py"},
                ),
                AgentResult(
                    agent_id="test_agent",
                    subtask_id="sub-002",
                    status="completed",
                    output="",
                    metadata={"test_file_path": "/new/path.py"},
                ),
            ]
        )
        result = invoke_mod._find_prior_metadata(state, "test_agent", "test_file_path")
        assert result == "/new/path.py"

    def test_returns_none_when_key_missing_from_metadata(self) -> None:
        state = _make_state(
            agent_results=[
                AgentResult(
                    agent_id="test_agent",
                    subtask_id="sub-001",
                    status="completed",
                    output="",
                    metadata={},
                )
            ]
        )
        result = invoke_mod._find_prior_metadata(state, "test_agent", "missing_key")
        assert result is None

    def test_prefix_match_works(self) -> None:
        state = _make_state(
            agent_results=[
                AgentResult(
                    agent_id="test_agent_v2",
                    subtask_id="sub-001",
                    status="completed",
                    output="",
                    metadata={"test_file_path": "/workspace/test.py"},
                )
            ]
        )
        result = invoke_mod._find_prior_metadata(state, "test_agent", "test_file_path")
        assert result == "/workspace/test.py"


class TestSecurityResultsAsDicts:
    def test_returns_only_security_agent_results(self) -> None:
        state = _make_state(
            agent_results=[
                AgentResult(
                    agent_id="security_agent",
                    subtask_id="sub-001",
                    status="completed",
                    output="[]",
                    metadata={"scan_complete": True},
                ),
                AgentResult(
                    agent_id="code_agent",
                    subtask_id="sub-002",
                    status="completed",
                    output="code",
                    metadata={},
                ),
            ]
        )
        result = invoke_mod._security_results_as_dicts(state)
        assert len(result) == 1
        assert result[0]["agent_id"] == "security_agent"

    def test_returns_empty_when_no_security_results(self) -> None:
        state = _make_state()
        result = invoke_mod._security_results_as_dicts(state)
        assert result == []

    def test_returns_dicts_not_typeddicts(self) -> None:
        state = _make_state(
            agent_results=[
                AgentResult(
                    agent_id="security_agent",
                    subtask_id="sub-001",
                    status="completed",
                    output="[]",
                    metadata={},
                )
            ]
        )
        result = invoke_mod._security_results_as_dicts(state)
        assert isinstance(result[0], dict)


# ---------------------------------------------------------------------------
# Invoke function unit tests
# ---------------------------------------------------------------------------


class TestInvokeTestAgent:
    async def test_returns_agent_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_test_agent_graph",
            _graph_mock({
                "status": "completed",
                "test_file_path": "/workspace/tests/test_feature.py",
                "test_code": "def test_foo(): pass",
                "tdd_phase": "green",
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_test_agent(state)
        assert len(result["agent_results"]) == 1
        assert result["agent_results"][0]["agent_id"] == "test_agent"
        assert result["agent_results"][0]["status"] == "completed"

    async def test_marks_subtask_completed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_test_agent_graph",
            _graph_mock({
                "status": "completed",
                "test_file_path": "/workspace/tests/test_feature.py",
                "test_code": "def test_foo(): pass",
                "tdd_phase": "green",
                "error": None,
            }),
        )
        state = _make_state(subtask_id="sub-001")
        result = await invoke_mod.invoke_test_agent(state)
        assert result["plan"][0]["status"] == "completed"

    async def test_stores_test_file_path_in_metadata(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_test_agent_graph",
            _graph_mock({
                "status": "completed",
                "test_file_path": "/workspace/tests/test_feature.py",
                "test_code": "def test_foo(): pass",
                "tdd_phase": "green",
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_test_agent(state)
        metadata = result["agent_results"][0]["metadata"]
        assert metadata["test_file_path"] == "/workspace/tests/test_feature.py"


class TestInvokeCodeAgent:
    async def test_propagates_test_file_path_from_prior_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_builder = _graph_mock({
            "status": "completed",
            "written_code": "def hello(): return True",
            "implementation_file_path": "/workspace/src/hello.py",
            "error": None,
        })
        monkeypatch.setattr(invoke_mod, "build_code_agent_graph", mock_builder)
        state = _make_state(
            agent_results=[
                AgentResult(
                    agent_id="test_agent",
                    subtask_id="sub-000",
                    status="completed",
                    output="",
                    metadata={"test_file_path": "/workspace/tests/test_feature.py"},
                )
            ]
        )
        result = await invoke_mod.invoke_code_agent(state)
        assert result["agent_results"][0]["metadata"]["test_file_path"] == (
            "/workspace/tests/test_feature.py"
        )

    async def test_stores_written_code_in_metadata(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_code_agent_graph",
            _graph_mock({
                "status": "completed",
                "written_code": "def hello(): return True",
                "implementation_file_path": "/workspace/src/hello.py",
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_code_agent(state)
        assert result["agent_results"][0]["metadata"]["written_code"] == (
            "def hello(): return True"
        )


class TestInvokeGitAgent:
    async def test_propagates_pr_url_to_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_git_agent_graph",
            _graph_mock({
                "status": "completed",
                "pr_url": "https://github.com/org/repo/pull/42",
                "commit_messages": [],
                "error": None,
            }),
        )
        state = _make_state(branch_name="feat/my-branch")
        result = await invoke_mod.invoke_git_agent(state)
        assert result["pr_url"] == "https://github.com/org/repo/pull/42"

    async def test_no_pr_url_key_when_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_git_agent_graph",
            _graph_mock({
                "status": "completed",
                "pr_url": None,
                "commit_messages": [],
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_git_agent(state)
        assert "pr_url" not in result

    async def test_passes_branch_name_to_agent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_builder = _graph_mock({
            "status": "completed",
            "pr_url": None,
            "commit_messages": [],
            "error": None,
        })
        monkeypatch.setattr(invoke_mod, "build_git_agent_graph", mock_builder)
        state = _make_state(branch_name="feat/specific-branch")
        await invoke_mod.invoke_git_agent(state)
        called_state = mock_builder.return_value.ainvoke.call_args[0][0]
        assert called_state["branch_name"] == "feat/specific-branch"


class TestInvokeSecurityAgent:
    async def test_stores_scan_metadata(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_security_agent_graph",
            _graph_mock({
                "status": "completed",
                "scan_complete": True,
                "secrets_detected": False,
                "sast_findings": [],
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_security_agent(state)
        metadata = result["agent_results"][0]["metadata"]
        assert metadata["scan_complete"] is True
        assert metadata["secrets_detected"] is False


class TestInvokeCodeReviewAgent:
    async def test_passes_security_results_to_agent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_builder = _graph_mock({
            "status": "completed",
            "review_result": {
                "approved": True,
                "reviewer_model": "mock",
                "comments": [],
                "blocking_issues": [],
                "metadata": {},
            },
            "error": None,
        })
        monkeypatch.setattr(invoke_mod, "build_code_review_agent_graph", mock_builder)
        state = _make_state(
            agent_results=[
                AgentResult(
                    agent_id="security_agent",
                    subtask_id="sub-000",
                    status="completed",
                    output="[]",
                    metadata={"scan_complete": True},
                )
            ]
        )
        await invoke_mod.invoke_code_review_agent(state)
        called_state = mock_builder.return_value.ainvoke.call_args[0][0]
        assert len(called_state["agent_results"]) == 1
        assert called_state["agent_results"][0]["agent_id"] == "security_agent"


class TestInvokeCicdAgent:
    async def test_returns_agent_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_cicd_agent_graph",
            _graph_mock({"status": "completed", "build_url": "https://ci/build/1", "error": None}),
        )
        state = _make_state()
        result = await invoke_mod.invoke_cicd_agent(state)
        assert result["agent_results"][0]["agent_id"] == "cicd_agent"
        assert result["agent_results"][0]["output"] == "https://ci/build/1"


class TestInvokeInfrastructureAgent:
    async def test_returns_manifest_paths_in_metadata(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_infrastructure_agent_graph",
            _graph_mock({
                "status": "completed",
                "manifests": [],
                "manifest_paths": ["/k8s/deploy.yaml"],
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_infrastructure_agent(state)
        assert result["agent_results"][0]["metadata"]["manifest_paths"] == ["/k8s/deploy.yaml"]


class TestInvokeArchitectureAgent:
    async def test_returns_adr_path_as_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_architecture_agent_graph",
            _graph_mock({
                "status": "completed",
                "adr_path": "/docs/adr/001-caching.md",
                "decision_rationale": "Use Redis for caching",
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_architecture_agent(state)
        assert result["agent_results"][0]["output"] == "/docs/adr/001-caching.md"

    async def test_falls_back_to_decision_rationale_when_no_adr(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_architecture_agent_graph",
            _graph_mock({
                "status": "completed",
                "adr_path": None,
                "decision_rationale": "Use Redis for caching",
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_architecture_agent(state)
        assert result["agent_results"][0]["output"] == "Use Redis for caching"


class TestInvokeDocsAgent:
    async def test_returns_file_paths_in_metadata(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_docs_agent_graph",
            _graph_mock({
                "status": "completed",
                "file_paths_updated": ["/docs/api.md"],
                "changelog_entry": "Added new endpoint",
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_docs_agent(state)
        assert result["agent_results"][0]["metadata"]["file_paths_updated"] == ["/docs/api.md"]


class TestInvokeDependencyAgent:
    async def test_returns_pr_urls_in_metadata(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_dependency_agent_graph",
            _graph_mock({
                "status": "completed",
                "pr_urls": ["https://github.com/org/repo/pull/10"],
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_dependency_agent(state)
        assert result["agent_results"][0]["metadata"]["pr_urls"] == [
            "https://github.com/org/repo/pull/10"
        ]


class TestInvokeIncidentResponseAgent:
    async def test_returns_jira_url_as_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_incident_response_agent_graph",
            _graph_mock({
                "status": "completed",
                "jira_issue_url": "https://jira.example.com/ISSUE-123",
                "runbook_path": "/runbooks/incident.md",
                "root_cause": "OOM on pod",
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_incident_response_agent(state)
        assert result["agent_results"][0]["output"] == "https://jira.example.com/ISSUE-123"

    async def test_falls_back_to_root_cause_when_no_jira_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_incident_response_agent_graph",
            _graph_mock({
                "status": "completed",
                "jira_issue_url": None,
                "runbook_path": None,
                "root_cause": "OOM on pod",
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_incident_response_agent(state)
        assert result["agent_results"][0]["output"] == "OOM on pod"

    async def test_stores_runbook_path_in_metadata(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            invoke_mod,
            "build_incident_response_agent_graph",
            _graph_mock({
                "status": "completed",
                "jira_issue_url": None,
                "runbook_path": "/runbooks/db-incident.md",
                "root_cause": "",
                "error": None,
            }),
        )
        state = _make_state()
        result = await invoke_mod.invoke_incident_response_agent(state)
        assert result["agent_results"][0]["metadata"]["runbook_path"] == "/runbooks/db-incident.md"
