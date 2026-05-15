"""Integration test fixtures for the full orchestrator + agent loop."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import orchestrator.nodes.invoke_agents as invoke_mod
import pytest
from dev_team_guardrail import GuardrailResult
from dev_team_state import OrchestratorState, TaskStatus
from langchain_core.messages import AIMessage

# ---------------------------------------------------------------------------
# State factory
# ---------------------------------------------------------------------------


def initial_state() -> OrchestratorState:
    return OrchestratorState(
        task_id="integ-001",
        task_description="Implement hello_world() function that returns 'Hello, World!'",
        plan=[],
        current_subtask=None,
        agent_results=[],
        human_approvals=[],
        run_id="run-integ-001",
        branch_name="feat/hello-world",
        pr_url=None,
        status=TaskStatus.PLANNING,
        messages=[],
        guardrail_passed=True,
    )


# ---------------------------------------------------------------------------
# Guardrail mocks
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# LLM mocks (task planner + context summariser)
# ---------------------------------------------------------------------------


def _make_mock_llm(subtasks: list[dict[str, Any]]) -> MagicMock:
    mock_structured = MagicMock()
    mock_structured.ainvoke = AsyncMock(return_value=subtasks)
    mock_llm = MagicMock()
    mock_llm.with_structured_output = MagicMock(return_value=mock_structured)
    return mock_llm


@pytest.fixture()
def mock_tdd_plan_llm(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Task planner returns a 4-subtask TDD plan: test→code→review→git."""
    subtasks = [
        {
            "subtask_id": "sub-001",
            "description": "Write failing tests for hello_world()",
            "agent_type": "test_agent",
            "requires_approval": False,
            "status": "planning",
        },
        {
            "subtask_id": "sub-002",
            "description": "Implement hello_world() to pass the tests",
            "agent_type": "code_agent",
            "requires_approval": False,
            "status": "planning",
        },
        {
            "subtask_id": "sub-003",
            "description": "Review code for hello_world()",
            "agent_type": "code_review_agent",
            "requires_approval": False,
            "status": "planning",
        },
        {
            "subtask_id": "sub-004",
            "description": "Create PR for hello_world() feature",
            "agent_type": "git_agent",
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
def mock_approval_plan_llm(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Task planner returns a single git_agent subtask that requires approval."""
    subtasks = [
        {
            "subtask_id": "sub-001",
            "description": "Create PR and merge to main",
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
def mock_security_then_review_plan_llm(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Task planner returns security_agent → code_review_agent plan."""
    subtasks = [
        {
            "subtask_id": "sub-001",
            "description": "Scan diff for security vulnerabilities",
            "agent_type": "security_agent",
            "requires_approval": False,
            "status": "planning",
        },
        {
            "subtask_id": "sub-002",
            "description": "Review code changes",
            "agent_type": "code_review_agent",
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
def mock_context_llm(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Summary of prior context."))
    monkeypatch.setattr(
        "orchestrator.nodes.context_summariser.init_chat_model",
        lambda *args, **kwargs: mock_llm,
    )
    return mock_llm


# ---------------------------------------------------------------------------
# Agent graph mocks
# ---------------------------------------------------------------------------


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
            "test_code": "def test_hello_world():\n    assert hello_world() == 'Hello, World!'\n",
            "tdd_phase": "green",
            "error": None,
        }),
    )
    monkeypatch.setattr(
        invoke_mod,
        "build_code_agent_graph",
        _graph_mock({
            "status": "completed",
            "written_code": "def hello_world() -> str:\n    return 'Hello, World!'\n",
            "implementation_file_path": "/workspace/src/hello_world.py",
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
            "commit_messages": ["feat(hello): add hello_world()"],
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
