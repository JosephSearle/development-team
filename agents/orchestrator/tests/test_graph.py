"""TDD tests for the full orchestrator graph wiring."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from dev_team_state import OrchestratorState, TaskStatus
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from orchestrator.graph import build_orchestrator_graph


def _initial_state() -> OrchestratorState:
    return OrchestratorState(
        task_id="task-001",
        task_description="Implement rate limiter middleware",
        plan=[],
        current_subtask=None,
        agent_results=[],
        human_approvals=[],
        run_id="run-001",
        branch_name="feat/rate-limiter",
        pr_url=None,
        status=TaskStatus.PLANNING,
        messages=[],
        guardrail_passed=False,
    )


class TestGraphGuardrailFails:
    async def test_graph_ends_after_guardrail_failure(
        self, mock_guardrail_fail: None
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "guardrail-fail-1"}}
        result = await graph.ainvoke(_initial_state(), config=config)
        assert result["guardrail_passed"] is False
        assert result["plan"] == []
        assert result["status"] == TaskStatus.PLANNING


class TestGraphSmoke:
    async def test_smoke_two_subtasks_complete(
        self, mock_guardrail_pass: None, mock_llm: MagicMock
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "smoke-1"}}
        result = await graph.ainvoke(_initial_state(), config=config)
        assert result["status"] == TaskStatus.COMPLETED
        assert len(result["agent_results"]) == 2
        assert result["guardrail_passed"] is True

    async def test_smoke_all_subtask_statuses_completed(
        self, mock_guardrail_pass: None, mock_llm: MagicMock
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "smoke-2"}}
        result = await graph.ainvoke(_initial_state(), config=config)
        for subtask in result["plan"]:
            assert subtask["status"] == "completed"


class TestGraphHITL:
    async def test_graph_pauses_for_approval(
        self, mock_guardrail_pass: None, mock_llm_with_approval_subtask: MagicMock
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "hitl-graph-1"}}
        result = await graph.ainvoke(_initial_state(), config=config)
        assert "__interrupt__" in result

    async def test_resume_completes_graph(
        self, mock_guardrail_pass: None, mock_llm_with_approval_subtask: MagicMock
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "hitl-graph-2"}}
        await graph.ainvoke(_initial_state(), config=config)
        result = await graph.ainvoke(
            Command(resume={"approved": True, "approved_by": "eng@test.com"}),
            config=config,
        )
        assert result["status"] == TaskStatus.COMPLETED
        assert result["human_approvals"][0]["approved"] is True


class TestGraphStreaming:
    async def test_astream_updates_yields_node_chunks(
        self, mock_guardrail_pass: None, mock_llm: MagicMock
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "stream-1"}}
        chunks: list[Any] = []
        async for chunk in graph.astream(_initial_state(), config=config, stream_mode="updates"):
            chunks.append(chunk)
        assert len(chunks) > 0
        assert all(isinstance(c, dict) for c in chunks)
        node_names = {k for chunk in chunks for k in chunk}
        assert "input_guardrail" in node_names

    async def test_astream_events_v3_yields_events(
        self, mock_guardrail_pass: None, mock_llm: MagicMock
    ) -> None:
        graph = build_orchestrator_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "stream-2"}}
        events: list[Any] = []
        async for event in graph.astream_events(
            _initial_state(), config=config, version="v2"
        ):
            events.append(event)
        assert len(events) > 0
        event_types = {e["event"] for e in events}
        assert any(t in event_types for t in ("on_chain_start", "on_chain_end"))
