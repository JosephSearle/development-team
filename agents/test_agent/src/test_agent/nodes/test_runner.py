"""test_runner node: executes pytest and captures structured results."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from dev_team_state.schema import TDDPhase, TestRunResult

from test_agent.schema import TestAgentState


async def _run_pytest(cmd: list[str]) -> tuple[int, str]:
    """Execute a pytest command and return (exit_code, stdout)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return proc.returncode or 0, stdout.decode()


def _parse_report(raw_output: str) -> TestRunResult:
    """Extract structured fields from pytest JSON report embedded in stdout."""
    json_blob: dict[str, Any] = {}
    for line in raw_output.splitlines():
        line = line.strip()
        if line.startswith("{") and "exitcode" in line:
            try:
                json_blob = json.loads(line)
                break
            except json.JSONDecodeError:
                pass

    if not json_blob:
        import contextlib
        with contextlib.suppress(json.JSONDecodeError):
            json_blob = json.loads(raw_output)

    summary = json_blob.get("summary", {})
    tests = json_blob.get("tests", [])
    failure_details = [
        t["nodeid"] for t in tests if t.get("outcome") in ("failed", "error")
    ]

    totals = json_blob.get("totals", {})
    line_pct: float | None = totals.get("percent_covered")
    branch_pct: float | None = None
    num_branches = totals.get("num_branches", 0)
    if num_branches:
        covered = totals.get("covered_branches", 0)
        branch_pct = round(covered / num_branches * 100, 2)

    return TestRunResult(
        exit_code=int(json_blob.get("exitcode", 1)),
        passed=int(summary.get("passed", 0)),
        failed=int(summary.get("failed", 0)),
        errors=int(summary.get("error", 0)),
        duration_seconds=float(json_blob.get("duration", 0.0)),
        coverage_line_pct=line_pct,
        coverage_branch_pct=branch_pct,
        failure_details=list(failure_details),
        raw_output=raw_output,
    )


async def test_runner(state: TestAgentState) -> dict[str, Any]:
    """Run pytest on the generated test file and update TDD phase."""
    test_path = state["test_file_path"]
    if not test_path:
        return {"status": "failed", "error": "No test file to run"}

    cmd = ["uv", "run", "pytest", test_path, "--tb=short", "-q"]
    exit_code, raw_output = await _run_pytest(cmd)
    results = _parse_report(raw_output)
    results["exit_code"] = exit_code
    results["raw_output"] = raw_output

    new_run_count = state["run_count"] + 1
    current_phase = state["tdd_phase"]

    if exit_code == 0 and current_phase == TDDPhase.RED:
        return {
            "test_results": results,
            "run_count": new_run_count,
            "tdd_phase": TDDPhase.RED,
            "error": "Tests passed immediately — strengthen assertions to ensure RED phase",
        }

    return {
        "test_results": results,
        "run_count": new_run_count,
        "tdd_phase": current_phase,
    }
