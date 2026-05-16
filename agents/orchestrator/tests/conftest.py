"""Shared fixtures for orchestrator tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import orchestrator.nodes.invoke_agents as invoke_mod
import pytest
from dev_team_guardrail import GuardrailResult
from dev_team_state import OrchestratorState, Subtask, TaskStatus
from dev_team_state.schema import AgentResult, HITLApproval
from langchain_core.messages import AIMessage


@pytest.fixture()
def minimal_subtask() -> Subtask:
    return Subtask(
        subtask_id="sub-001",
        description="Write failing tests for rate limiter",
        agent_type="code_agent",
        requires_approval=False,
        status=TaskStatus.PLANNING.value,
    )


@pytest.fixture()
def approval_subtask() -> Subtask:
    return Subtask(
        subtask_id="sub-001",
        description="Deploy to production",
        agent_type="git_agent",
        requires_approval=True,
        status=TaskStatus.PLANNING.value,
    )


@pytest.fixture()
def minimal_state(minimal_subtask: Subtask) -> OrchestratorState:
    return OrchestratorState(
        task_id="task-001",
        task_description="Implement rate limiter middleware",
        plan=[minimal_subtask],
        current_subtask=minimal_subtask,
        agent_results=[],
        human_approvals=[],
        run_id="run-001",
        branch_name="feat/rate-limiter",
        pr_url=None,
        status=TaskStatus.IN_PROGRESS,
        messages=[],
        guardrail_passed=False,
    )


@pytest.fixture()
def pre_planning_state() -> OrchestratorState:
    return OrchestratorState(
        task_id="task-002",
        task_description="Add authentication to API endpoints",
        plan=[],
        current_subtask=None,
        agent_results=[],
        human_approvals=[],
        run_id="run-002",
        branch_name="feat/auth",
        pr_url=None,
        status=TaskStatus.PLANNING,
        messages=[],
        guardrail_passed=True,
    )


@pytest.fixture()
def mock_guardrail_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _screen(self: Any, text: str) -> GuardrailResult:
        return GuardrailResult(passed=True, category=None)

    monkeypatch.setattr(
        "orchestrator.nodes.input_guardrail.GuardrailClient.screen",
        _screen,
    )


@pytest.fixture()
def mock_guardrail_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _screen(self: Any, text: str) -> GuardrailResult:
        return GuardrailResult(passed=False, category="S2")

    monkeypatch.setattr(
        "orchestrator.nodes.input_guardrail.GuardrailClient.screen",
        _screen,
    )


def _make_mock_llm(subtasks: list[dict[str, Any]]) -> MagicMock:
    mock_structured = MagicMock()
    mock_structured.ainvoke = AsyncMock(return_value=subtasks)
    mock_llm = MagicMock()
    mock_llm.with_structured_output = MagicMock(return_value=mock_structured)
    return mock_llm


@pytest.fixture()
def mock_llm(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    subtasks = [
        {
            "subtask_id": "sub-001",
            "description": "Write failing tests",
            "agent_type": "test_agent",
            "requires_approval": False,
            "status": "planning",
        },
        {
            "subtask_id": "sub-002",
            "description": "Implement feature",
            "agent_type": "code_agent",
            "requires_approval": False,
            "status": "planning",
        },
    ]
    llm = _make_mock_llm(subtasks)
    monkeypatch.setattr(
        "orchestrator.nodes.task_planner.init_chat_model",
        lambda *args, **kwargs: llm,
    )
    return llm


@pytest.fixture()
def mock_llm_with_approval_subtask(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    subtasks = [
        {
            "subtask_id": "sub-001",
            "description": "Merge to main and deploy",
            "agent_type": "git_agent",
            "requires_approval": True,
            "status": "planning",
        },
    ]
    llm = _make_mock_llm(subtasks)
    monkeypatch.setattr(
        "orchestrator.nodes.task_planner.init_chat_model",
        lambda *args, **kwargs: llm,
    )
    return llm


@pytest.fixture()
def mock_context_llm(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Summary of prior context."))
    monkeypatch.setattr(
        "orchestrator.nodes.context_summariser.init_chat_model",
        lambda *args, **kwargs: mock_llm,
    )
    return mock_llm


def _graph_mock(terminal_state: dict[str, Any]) -> MagicMock:
    graph = MagicMock()
    graph.ainvoke = AsyncMock(return_value=terminal_state)
    builder = MagicMock(return_value=graph)
    return builder


@pytest.fixture()
def mock_all_agent_graphs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch all build_*_graph callables in invoke_agents with fast mock graphs."""
    monkeypatch.setattr(
        invoke_mod,
        "build_test_agent_graph",
        _graph_mock({
            "status": "completed",
            "test_file_path": "/workspace/tests/test_feature.py",
            "test_code": "def test_hello():\n    assert True\n",
            "tdd_phase": "green",
            "error": None,
        }),
    )
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
    monkeypatch.setattr(
        invoke_mod,
        "build_code_review_agent_graph",
        _graph_mock({
            "status": "completed",
            "review_result": {
                "approved": True,
                "reviewer_model": "mock",
                "comments": [],
                "blocking_issues": [],
                "metadata": {},
            },
            "error": None,
        }),
    )
    monkeypatch.setattr(
        invoke_mod,
        "build_git_agent_graph",
        _graph_mock({
            "status": "completed",
            "pr_url": "https://github.com/org/repo/pull/1",
            "commit_messages": ["feat: add feature"],
            "error": None,
        }),
    )
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
    monkeypatch.setattr(
        invoke_mod,
        "build_cicd_agent_graph",
        _graph_mock({"status": "completed", "build_url": "", "error": None}),
    )
    monkeypatch.setattr(
        invoke_mod,
        "build_infrastructure_agent_graph",
        _graph_mock({"status": "completed", "manifests": [], "manifest_paths": [], "error": None}),
    )
    monkeypatch.setattr(
        invoke_mod,
        "build_architecture_agent_graph",
        _graph_mock(
            {"status": "completed", "adr_path": "", "decision_rationale": "", "error": None}
        ),
    )
    monkeypatch.setattr(
        invoke_mod,
        "build_docs_agent_graph",
        _graph_mock(
            {"status": "completed", "file_paths_updated": [], "changelog_entry": "", "error": None}
        ),
    )
    monkeypatch.setattr(
        invoke_mod,
        "build_dependency_agent_graph",
        _graph_mock({"status": "completed", "pr_urls": [], "error": None}),
    )
    monkeypatch.setattr(
        invoke_mod,
        "build_incident_response_agent_graph",
        _graph_mock({
            "status": "completed",
            "jira_issue_url": None,
            "runbook_path": None,
            "root_cause": "",
            "error": None,
        }),
    )


def _make_agent_result(agent_id: str, subtask_id: str) -> AgentResult:
    return AgentResult(
        agent_id=agent_id,
        subtask_id=subtask_id,
        status="completed",
        output=f"Output from {agent_id}",
        metadata={},
    )


def _make_hitl_approval(checkpoint_id: str, approved: bool) -> HITLApproval:
    return HITLApproval(
        checkpoint_id=checkpoint_id,
        approved=approved,
        approved_by="test@example.com",
        timestamp="2026-05-13T10:00:00Z",
    )
