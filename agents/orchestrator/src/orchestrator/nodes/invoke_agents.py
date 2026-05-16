"""Orchestrator invoke node functions.

Translates OrchestratorState to/from each specialist agent's state schema.
"""

from __future__ import annotations

import os
from typing import Any

# Graph builders imported at module top so tests can monkeypatch by name.
from architecture_agent.graph import build_architecture_agent_graph
from architecture_agent.schema import ArchitectureAgentState
from cicd_agent.graph import build_cicd_agent_graph
from cicd_agent.schema import CICDAgentState
from code_agent.graph import build_code_agent_graph
from code_agent.schema import CodeAgentState
from code_review_agent.graph import build_code_review_agent_graph
from code_review_agent.schema import CodeReviewAgentState
from dependency_agent.graph import build_dependency_agent_graph
from dependency_agent.schema import DependencyAgentState
from dev_team_state import OrchestratorState
from dev_team_state.schema import AgentResult, TDDPhase
from docs_agent.graph import build_docs_agent_graph
from docs_agent.schema import DocsAgentState
from git_agent.graph import build_git_agent_graph
from git_agent.schema import GitAgentState
from incident_response_agent.graph import build_incident_response_agent_graph
from incident_response_agent.schema import IncidentResponseAgentState
from infrastructure_agent.graph import build_infrastructure_agent_graph
from infrastructure_agent.schema import InfrastructureAgentState
from security_agent.graph import build_security_agent_graph
from security_agent.schema import SecurityAgentState
from test_agent.graph import build_test_agent_graph
from test_agent.schema import TestAgentState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mark_completed(plan: list[Any], subtask_id: str) -> list[Any]:
    return [{**s, "status": "completed"} if s["subtask_id"] == subtask_id else s for s in plan]


def _find_prior_metadata(state: OrchestratorState, agent_id_prefix: str, key: str) -> str | None:
    for r in reversed(state["agent_results"]):
        if str(r["agent_id"]).startswith(agent_id_prefix):
            metadata = r.get("metadata") or {}
            val = metadata.get(key) if isinstance(metadata, dict) else None
            return str(val) if val is not None else None
    return None


def _security_results_as_dicts(state: OrchestratorState) -> list[dict[str, object]]:
    """Return prior security AgentResult entries as plain dicts for CodeReviewAgentState."""
    return [
        dict(r)
        for r in state["agent_results"]
        if str(r["agent_id"]).startswith("security_agent")
    ]


# ---------------------------------------------------------------------------
# Invoke functions — one per specialist agent
# ---------------------------------------------------------------------------


async def invoke_test_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    agent_state: TestAgentState = {
        "subtask_id": subtask["subtask_id"],
        "feature_spec": subtask["description"],
        "tdd_phase": TDDPhase.SETUP,
        "test_file_path": None,
        "test_code": None,
        "test_results": None,
        "run_count": 0,
        "flaky_test_ids": [],
        "guardrail_passed": True,
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_test_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    return {
        "agent_results": [
            AgentResult(
                agent_id="test_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=result.get("test_code") or "",
                metadata={
                    "test_file_path": result.get("test_file_path") or "",
                    "tdd_phase": str(result.get("tdd_phase") or ""),
                },
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }


async def invoke_code_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    agent_state: CodeAgentState = {
        "subtask_id": subtask["subtask_id"],
        "feature_spec": subtask["description"],
        "tdd_phase": TDDPhase.RED,
        "test_file_path": _find_prior_metadata(state, "test_agent", "test_file_path"),
        "test_results": None,
        "written_code": None,
        "implementation_file_path": None,
        "guardrail_passed": True,
        "messages": [],
        "status": "in_progress",
        "error": None,
        "iteration_count": 0,
    }
    graph = build_code_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    return {
        "agent_results": [
            AgentResult(
                agent_id="code_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=result.get("written_code") or "",
                metadata={
                    "written_code": result.get("written_code") or "",
                    "implementation_file_path": result.get("implementation_file_path") or "",
                    "test_file_path": _find_prior_metadata(state, "test_agent", "test_file_path")
                    or "",
                },
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }


async def invoke_code_review_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    agent_state: CodeReviewAgentState = {
        "subtask_id": subtask["subtask_id"],
        "feature_spec": subtask["description"],
        "tdd_phase": TDDPhase.GREEN,
        "written_code": _find_prior_metadata(state, "code_agent", "written_code"),
        "test_results": None,
        "agent_results": _security_results_as_dicts(state),
        "scan_complete": False,
        "review_result": None,
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_code_review_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    review: dict[str, Any] = result.get("review_result") or {}
    return {
        "agent_results": [
            AgentResult(
                agent_id="code_review_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=str(review.get("comments", [])),
                metadata={
                    "approved": review.get("approved", False),
                    "blocking_issues": review.get("blocking_issues", []),
                },
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }


async def invoke_git_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    agent_state: GitAgentState = {
        "subtask_id": subtask["subtask_id"],
        "task_description": subtask["description"],
        "branch_name": state["branch_name"],
        "pr_url": state.get("pr_url"),
        "commit_messages": [],
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_git_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    update: dict[str, Any] = {
        "agent_results": [
            AgentResult(
                agent_id="git_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=result.get("pr_url") or "",
                metadata={"pr_url": result.get("pr_url") or ""},
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }
    if result.get("pr_url"):
        update["pr_url"] = result["pr_url"]
    return update


async def invoke_security_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    agent_state: SecurityAgentState = {
        "subtask_id": subtask["subtask_id"],
        "diff_content": subtask["description"],
        "secrets_detected": False,
        "scan_complete": False,
        "sast_findings": [],
        "guardrail_passed": True,
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_security_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    return {
        "agent_results": [
            AgentResult(
                agent_id="security_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=str(result.get("sast_findings", [])),
                metadata={
                    "scan_complete": result.get("scan_complete", False),
                    "secrets_detected": result.get("secrets_detected", False),
                },
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }


async def invoke_cicd_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None

    agent_state: CICDAgentState = {
        "subtask_id": subtask["subtask_id"],
        "task_description": subtask["description"],
        "pipeline_type": None,
        "build_url": None,
        "deployment_env": None,
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_cicd_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    return {
        "agent_results": [
            AgentResult(
                agent_id="cicd_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=result.get("build_url") or "",
                metadata={"build_url": result.get("build_url") or ""},
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }


async def invoke_infrastructure_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    agent_state: InfrastructureAgentState = {
        "subtask_id": subtask["subtask_id"],
        "task_description": subtask["description"],
        "manifests": [],
        "manifest_paths": [],
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_infrastructure_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    return {
        "agent_results": [
            AgentResult(
                agent_id="infrastructure_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=str(result.get("manifest_paths", [])),
                metadata={"manifest_paths": result.get("manifest_paths", [])},
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }


async def invoke_architecture_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    workspace_base = os.getenv("WORKSPACE_DIR", "/tmp/dev-team")
    agent_state: ArchitectureAgentState = {
        "subtask_id": subtask["subtask_id"],
        "task_description": subtask["description"],
        "workspace": os.path.join(workspace_base, subtask["subtask_id"]),
        "decision_rationale": "",
        "options_evaluated": [],
        "adr_path": None,
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_architecture_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    return {
        "agent_results": [
            AgentResult(
                agent_id="architecture_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=result.get("adr_path") or result.get("decision_rationale") or "",
                metadata={"adr_path": result.get("adr_path") or ""},
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }


async def invoke_docs_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    workspace_base = os.getenv("WORKSPACE_DIR", "/tmp/dev-team")
    agent_state: DocsAgentState = {
        "subtask_id": subtask["subtask_id"],
        "task_description": subtask["description"],
        "workspace": os.path.join(workspace_base, subtask["subtask_id"]),
        "file_paths_updated": [],
        "changelog_entry": "",
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_docs_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    return {
        "agent_results": [
            AgentResult(
                agent_id="docs_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=str(result.get("file_paths_updated", [])),
                metadata={"file_paths_updated": result.get("file_paths_updated", [])},
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }


async def invoke_dependency_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    agent_state: DependencyAgentState = {
        "subtask_id": subtask["subtask_id"],
        "task_description": subtask["description"],
        "dependencies_scanned": [],
        "vulnerabilities_found": [],
        "upgrades_proposed": [],
        "pr_urls": [],
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_dependency_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    return {
        "agent_results": [
            AgentResult(
                agent_id="dependency_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=str(result.get("pr_urls", [])),
                metadata={"pr_urls": result.get("pr_urls", [])},
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }


async def invoke_incident_response_agent(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    assert subtask is not None
    agent_state: IncidentResponseAgentState = {
        "subtask_id": subtask["subtask_id"],
        "task_description": subtask["description"],
        "alert_context": subtask["description"],
        "root_cause": "",
        "remediation_steps": [],
        "jira_issue_url": None,
        "runbook_path": None,
        "messages": [],
        "status": "in_progress",
        "error": None,
    }
    graph = build_incident_response_agent_graph()
    result: dict[str, Any] = await graph.ainvoke(
        agent_state,
        config={"configurable": {"thread_id": subtask["subtask_id"]}},
    )
    return {
        "agent_results": [
            AgentResult(
                agent_id="incident_response_agent",
                subtask_id=subtask["subtask_id"],
                status=result["status"],
                output=result.get("jira_issue_url") or result.get("root_cause") or "",
                metadata={
                    "jira_issue_url": result.get("jira_issue_url") or "",
                    "runbook_path": result.get("runbook_path") or "",
                },
            )
        ],
        "plan": _mark_completed(state["plan"], subtask["subtask_id"]),
    }
