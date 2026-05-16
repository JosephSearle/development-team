from __future__ import annotations

from typing import Any

from dev_team_state import OrchestratorState, TaskStatus
from dev_team_state.schema import HITLApproval
from langgraph.types import interrupt


def hitl_gate(state: OrchestratorState) -> dict[str, Any]:
    subtask = state["current_subtask"]
    if subtask is None or not subtask["requires_approval"]:
        return {}
    response: dict[str, Any] = interrupt(
        {
            "subtask_id": subtask["subtask_id"],
            "description": subtask["description"],
            "agent_type": subtask["agent_type"],
            "message": "Approve this subtask before execution?",
        }
    )
    record = HITLApproval(
        checkpoint_id=subtask["subtask_id"],
        approved=bool(response.get("approved", False)),
        approved_by=response.get("approved_by"),
        timestamp=response.get("timestamp"),
    )
    return {
        "human_approvals": [*state["human_approvals"], record],
        "status": TaskStatus.IN_PROGRESS,
    }
