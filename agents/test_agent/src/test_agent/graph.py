"""Test Agent LangGraph graph: RED → coverage_checker → flake_detector TDD state machine."""

from __future__ import annotations

from typing import Any

from dev_team_state.schema import TDDPhase
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from test_agent.nodes.coverage_checker import coverage_checker
from test_agent.nodes.flake_detector import flake_detector
from test_agent.nodes.test_runner import test_runner
from test_agent.nodes.test_writer import test_writer
from test_agent.schema import TestAgentState


def _route_after_test_runner(state: TestAgentState) -> str:
    if state.get("status") == "failed":
        return END
    results = state["test_results"]
    if results is None:
        return "test_writer"
    if results["exit_code"] == 0 and state["tdd_phase"] == TDDPhase.RED:
        return "test_writer"
    if results["exit_code"] != 0 and state["tdd_phase"] == TDDPhase.RED:
        return "coverage_checker"
    return "test_writer"


def _route_after_coverage(state: TestAgentState) -> str:
    if state.get("status") == "failed":
        return "test_writer"
    return "flake_detector"


def build_test_agent_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph:  # type: ignore[type-arg]
    builder: StateGraph[TestAgentState] = StateGraph(TestAgentState)

    builder.add_node("test_writer", test_writer)
    builder.add_node("test_runner", test_runner)
    builder.add_node("coverage_checker", coverage_checker)
    builder.add_node("flake_detector", flake_detector)

    builder.add_edge(START, "test_writer")
    builder.add_conditional_edges(
        "test_writer",
        lambda s: END if s.get("status") == "failed" else "test_runner",
        {"test_runner": "test_runner", END: END},
    )
    builder.add_conditional_edges(
        "test_runner",
        _route_after_test_runner,
        {
            "test_writer": "test_writer",
            "coverage_checker": "coverage_checker",
            END: END,
        },
    )
    builder.add_conditional_edges(
        "coverage_checker",
        _route_after_coverage,
        {"test_writer": "test_writer", "flake_detector": "flake_detector"},
    )
    builder.add_edge("flake_detector", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
