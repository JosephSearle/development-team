"""scan_gate node — blocks code review until security scan is confirmed complete."""

from __future__ import annotations

from typing import Any

from code_review_agent.schema import CodeReviewAgentState


def scan_gate(state: CodeReviewAgentState) -> dict[str, Any]:
    for entry in state.get("agent_results", []):
        agent_id = str(entry.get("agent_id", ""))
        if agent_id.startswith("security_agent"):
            metadata = entry.get("metadata") or {}
            if isinstance(metadata, dict) and metadata.get("scan_complete") is True:
                return {"scan_complete": True}

    return {
        "scan_complete": False,
        "status": "failed",
        "error": "Security scan not complete — code review blocked",
    }
