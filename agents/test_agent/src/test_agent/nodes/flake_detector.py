"""flake_detector node: identifies intermittent test failures across multiple runs."""

from __future__ import annotations

import json
from typing import Any

from dev_team_state.schema import TDDPhase

from test_agent.nodes.test_runner import _run_pytest
from test_agent.schema import TestAgentState

FLAKE_RUN_COUNT: int = 3


def _extract_failure_ids(raw_output: str) -> set[str]:
    """Parse failure test IDs from a pytest JSON report embedded in stdout."""
    for line in raw_output.splitlines():
        line = line.strip()
        if line.startswith("{") and "tests" in line:
            try:
                blob = json.loads(line)
                return {
                    t["nodeid"]
                    for t in blob.get("tests", [])
                    if t.get("outcome") in ("failed", "error")
                }
            except json.JSONDecodeError:
                pass
    try:
        blob = json.loads(raw_output)
        return {
            t["nodeid"]
            for t in blob.get("tests", [])
            if t.get("outcome") in ("failed", "error")
        }
    except json.JSONDecodeError:
        return set()


async def flake_detector(state: TestAgentState) -> dict[str, Any]:
    """Run the test suite FLAKE_RUN_COUNT times and flag intermittent failures."""
    test_path = state["test_file_path"]
    if not test_path:
        return {"status": "completed", "flaky_test_ids": [], "tdd_phase": TDDPhase.GREEN}

    cmd = ["uv", "run", "pytest", test_path, "--tb=line", "-q"]
    all_failures: list[set[str]] = []
    for _ in range(FLAKE_RUN_COUNT):
        _, raw = await _run_pytest(cmd)
        all_failures.append(_extract_failure_ids(raw))

    all_seen = set().union(*all_failures)
    always_failed = all_seen.copy()
    for run_failures in all_failures:
        always_failed &= run_failures

    flaky = sorted(all_seen - always_failed)

    result: dict[str, Any] = {
        "flaky_test_ids": flaky,
        "tdd_phase": TDDPhase.GREEN,
        "status": "completed",
    }
    if flaky:
        result["error"] = f"Flaky tests detected: {', '.join(flaky)}"

    return result
