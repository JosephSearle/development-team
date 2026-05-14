"""CodeAgentState TypedDict for the Code Agent LangGraph graph."""

from __future__ import annotations

from typing import Annotated

from dev_team_state.schema import TDDPhase, TestRunResult
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class CodeAgentState(TypedDict):
    """Full LangGraph state for the Code Agent graph."""

    subtask_id: str
    feature_spec: str
    tdd_phase: TDDPhase
    test_file_path: str | None
    test_results: TestRunResult | None
    written_code: str | None
    implementation_file_path: str | None
    guardrail_passed: bool
    messages: Annotated[list[AnyMessage], add_messages]
    status: str
    error: str | None
    iteration_count: int
