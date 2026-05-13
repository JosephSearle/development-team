"""TDD tests for the task_planner node."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from dev_team_state import OrchestratorState, TaskStatus
from langchain_core.messages import HumanMessage
from orchestrator.nodes.task_planner import task_planner


class TestTaskPlannerOutputShape:
    async def test_plan_is_list_of_subtasks(
        self, mock_llm: MagicMock, pre_planning_state: OrchestratorState
    ) -> None:
        result = await task_planner(pre_planning_state)
        assert isinstance(result["plan"], list)
        assert len(result["plan"]) > 0
        required_keys = {"subtask_id", "description", "agent_type", "requires_approval", "status"}
        for subtask in result["plan"]:
            assert required_keys.issubset(subtask.keys())

    async def test_status_set_to_in_progress(
        self, mock_llm: MagicMock, pre_planning_state: OrchestratorState
    ) -> None:
        result = await task_planner(pre_planning_state)
        assert result["status"] == TaskStatus.IN_PROGRESS

    async def test_current_subtask_set_to_first_plan_item(
        self, mock_llm: MagicMock, pre_planning_state: OrchestratorState
    ) -> None:
        result = await task_planner(pre_planning_state)
        assert result["current_subtask"] == result["plan"][0]

    async def test_adds_human_message_to_messages(
        self, mock_llm: MagicMock, pre_planning_state: OrchestratorState
    ) -> None:
        result = await task_planner(pre_planning_state)
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], HumanMessage)
        assert pre_planning_state["task_description"] in result["messages"][0].content


class TestTaskPlannerLLMCall:
    async def test_init_chat_model_called_with_correct_model(
        self, monkeypatch: pytest.MonkeyPatch, pre_planning_state: OrchestratorState
    ) -> None:
        captured_args: list[Any] = []

        from unittest.mock import AsyncMock, MagicMock

        def fake_init_chat_model(model: str, **kwargs: Any) -> MagicMock:
            captured_args.append(model)
            mock_structured = MagicMock()
            mock_structured.ainvoke = AsyncMock(
                return_value=[
                    {
                        "subtask_id": "sub-001",
                        "description": "Do something",
                        "agent_type": "code_agent",
                        "requires_approval": False,
                        "status": "planning",
                    }
                ]
            )
            mock_llm = MagicMock()
            mock_llm.with_structured_output = MagicMock(return_value=mock_structured)
            return mock_llm

        monkeypatch.setattr("orchestrator.nodes.task_planner.init_chat_model", fake_init_chat_model)
        await task_planner(pre_planning_state)
        assert captured_args == ["openai:qwen3.5-72b-instruct"]

    async def test_with_structured_output_called(
        self, mock_llm: MagicMock, pre_planning_state: OrchestratorState
    ) -> None:
        await task_planner(pre_planning_state)
        mock_llm.with_structured_output.assert_called_once()


class TestTaskPlannerSubtaskIds:
    async def test_subtasks_have_generated_ids_if_missing(
        self, monkeypatch: pytest.MonkeyPatch, pre_planning_state: OrchestratorState
    ) -> None:
        from unittest.mock import AsyncMock, MagicMock

        subtasks_no_id = [
            {
                "description": "Write tests",
                "agent_type": "test_agent",
                "requires_approval": False,
                "status": "planning",
            }
        ]
        mock_structured = MagicMock()
        mock_structured.ainvoke = AsyncMock(return_value=subtasks_no_id)
        mock_llm = MagicMock()
        mock_llm.with_structured_output = MagicMock(return_value=mock_structured)
        monkeypatch.setattr(
            "orchestrator.nodes.task_planner.init_chat_model",
            lambda *a, **kw: mock_llm,
        )
        result = await task_planner(pre_planning_state)
        assert result["plan"][0]["subtask_id"] == "sub-001"
