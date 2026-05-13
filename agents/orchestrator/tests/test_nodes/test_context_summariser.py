"""TDD tests for the context_summariser node."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from dev_team_state import OrchestratorState, TaskStatus
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from orchestrator.nodes.context_summariser import context_summariser


def _state_with_messages(messages: list[Any]) -> OrchestratorState:
    return OrchestratorState(
        task_id="task-001",
        task_description="Test",
        plan=[],
        current_subtask=None,
        agent_results=[],
        human_approvals=[],
        run_id="run-001",
        branch_name="main",
        pr_url=None,
        status=TaskStatus.IN_PROGRESS,
        messages=messages,
        guardrail_passed=True,
    )


def _make_messages(n: int) -> list[HumanMessage]:
    return [HumanMessage(content=f"Message {i}", id=f"msg-{i}") for i in range(n)]


class TestContextSummariserThreshold:
    async def test_no_op_below_threshold(
        self, mock_context_llm: MagicMock
    ) -> None:
        state = _state_with_messages(_make_messages(3))
        result = await context_summariser(state)
        assert result == {}
        mock_context_llm.ainvoke.assert_not_called()

    async def test_no_op_at_exactly_threshold(
        self, mock_context_llm: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("orchestrator.nodes.context_summariser.MESSAGE_THRESHOLD", 10)
        state = _state_with_messages(_make_messages(10))
        result = await context_summariser(state)
        assert result == {}

    async def test_summarises_above_threshold(
        self, mock_context_llm: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("orchestrator.nodes.context_summariser.MESSAGE_THRESHOLD", 10)
        state = _state_with_messages(_make_messages(11))
        result = await context_summariser(state)
        assert "messages" in result
        msgs = result["messages"]
        remove_ops = [m for m in msgs if isinstance(m, RemoveMessage)]
        summary_msgs = [m for m in msgs if isinstance(m, AIMessage)]
        assert len(remove_ops) == 11
        assert len(summary_msgs) == 1
        assert summary_msgs[0].content == "Summary of prior context."

    async def test_threshold_configurable_via_module_attr(
        self, mock_context_llm: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("orchestrator.nodes.context_summariser.MESSAGE_THRESHOLD", 5)
        state = _state_with_messages(_make_messages(6))
        result = await context_summariser(state)
        assert "messages" in result

    async def test_messages_without_ids_not_included_in_remove_ops(
        self, mock_context_llm: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("orchestrator.nodes.context_summariser.MESSAGE_THRESHOLD", 2)
        no_id_msgs = [HumanMessage(content=f"msg {i}") for i in range(3)]
        state = _state_with_messages(no_id_msgs)
        result = await context_summariser(state)
        remove_ops = [m for m in result["messages"] if isinstance(m, RemoveMessage)]
        assert len(remove_ops) == 0
