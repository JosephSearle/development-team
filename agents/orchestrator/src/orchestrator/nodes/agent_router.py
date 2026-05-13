from __future__ import annotations

from typing import Any

from dev_team_state import OrchestratorState, TaskStatus
from langgraph.graph import END

_AGENT_NODE_MAP: dict[str, str] = {
    "code_agent": "invoke_code_agent",
    "test_agent": "invoke_test_agent",
    "code_review_agent": "invoke_code_review_agent",
    "git_agent": "invoke_git_agent",
    "architecture_agent": "invoke_architecture_agent",
    "cicd_agent": "invoke_cicd_agent",
    "security_agent": "invoke_security_agent",
    "docs_agent": "invoke_docs_agent",
    "infrastructure_agent": "invoke_infrastructure_agent",
    "dependency_agent": "invoke_dependency_agent",
    "incident_response_agent": "invoke_incident_response_agent",
}


def agent_router(state: OrchestratorState) -> dict[str, Any]:
    pending = [s for s in state["plan"] if s["status"] != "completed"]
    if not pending:
        return {"current_subtask": None, "status": TaskStatus.COMPLETED}
    return {"current_subtask": pending[0]}


def route_to_agent(state: OrchestratorState) -> str:
    subtask = state["current_subtask"]
    if subtask is None:
        return END
    node_name = _AGENT_NODE_MAP.get(subtask["agent_type"])
    if node_name is None:
        raise ValueError(f"Unknown agent_type: {subtask['agent_type']!r}")
    return node_name
