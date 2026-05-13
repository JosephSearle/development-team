from __future__ import annotations

import os
from typing import Any, cast

from dev_team_state import OrchestratorState, Subtask, TaskStatus
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from orchestrator.prompts.task_planner import TASK_PLANNER_SYSTEM_PROMPT


async def task_planner(state: OrchestratorState) -> dict[str, Any]:
    llm = init_chat_model(
        "openai:qwen3.5-72b-instruct",
        base_url=os.environ.get("VLLM_REASONING_URL", "http://vllm-reasoning:8000"),
        api_key="EMPTY",
        temperature=0,
    )
    structured = llm.with_structured_output(list[Subtask])
    human_msg = HumanMessage(content=state["task_description"])
    plan: list[Subtask] = cast(
        list[Subtask],
        await structured.ainvoke(
            [{"role": "system", "content": TASK_PLANNER_SYSTEM_PROMPT}, human_msg]
        ),
    )
    for i, subtask in enumerate(plan):
        if not subtask.get("subtask_id"):
            subtask["subtask_id"] = f"sub-{i + 1:03d}"
        subtask["status"] = TaskStatus.PLANNING.value
    return {
        "plan": plan,
        "current_subtask": plan[0],
        "status": TaskStatus.IN_PROGRESS,
        "messages": [human_msg],
    }
