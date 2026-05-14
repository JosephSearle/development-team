"""Code Review Agent state schema."""

from __future__ import annotations

from typing import Annotated, TypedDict

from dev_team_state.schema import CodeReviewResult, TDDPhase, TestRunResult
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class CodeReviewAgentState(TypedDict):
    subtask_id: str
    feature_spec: str
    tdd_phase: TDDPhase
    written_code: str | None
    test_results: TestRunResult | None
    agent_results: list[dict[str, object]]
    scan_complete: bool
    review_result: CodeReviewResult | None
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
