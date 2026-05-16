"""TestAgentState TypedDict for the Test Agent LangGraph graph."""

from __future__ import annotations

from typing import Annotated

from dev_team_state.schema import TDDPhase, TestRunResult
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class TestAgentState(TypedDict):
    """Full LangGraph state for the Test Agent graph."""

    subtask_id: str
    feature_spec: str
    tdd_phase: TDDPhase
    test_file_path: str | None
    test_code: str | None
    test_results: TestRunResult | None
    run_count: int
    flaky_test_ids: list[str]
    guardrail_passed: bool
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
