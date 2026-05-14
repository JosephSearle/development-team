"""coverage_checker node: asserts test coverage meets configured thresholds."""

from __future__ import annotations

from typing import Any

from dev_team_state.schema import TDDPhase

from test_agent.schema import TestAgentState

LINE_COVERAGE_THRESHOLD: float = 80.0
BRANCH_COVERAGE_THRESHOLD: float = 70.0


def coverage_checker(state: TestAgentState) -> dict[str, Any]:
    """Check coverage thresholds; advance to GREEN or fail with details."""
    results = state["test_results"]
    if results is None:
        return {}

    line_pct = results["coverage_line_pct"]
    branch_pct = results["coverage_branch_pct"]

    line_ok = line_pct is None or line_pct >= LINE_COVERAGE_THRESHOLD
    branch_ok = branch_pct is None or branch_pct >= BRANCH_COVERAGE_THRESHOLD

    if line_ok and branch_ok:
        return {"tdd_phase": TDDPhase.GREEN}

    parts = []
    if not line_ok:
        parts.append(f"line={line_pct:.1f}% (need {LINE_COVERAGE_THRESHOLD:.0f}%)")
    if not branch_ok:
        parts.append(f"branch={branch_pct:.1f}% (need {BRANCH_COVERAGE_THRESHOLD:.0f}%)")

    return {
        "status": "failed",
        "error": f"Coverage below threshold: {', '.join(parts)}",
    }
