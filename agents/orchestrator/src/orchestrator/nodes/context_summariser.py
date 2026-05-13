from __future__ import annotations

import os
from typing import Any

from dev_team_state import OrchestratorState
from langchain.chat_models import init_chat_model
from langchain_core.messages import AnyMessage, RemoveMessage

from orchestrator.prompts.context_summariser import CONTEXT_SUMMARISER_SYSTEM_PROMPT

MESSAGE_THRESHOLD: int = int(os.environ.get("MESSAGE_THRESHOLD", "50"))


async def context_summariser(state: OrchestratorState) -> dict[str, Any]:
    messages: list[AnyMessage] = state["messages"]
    if len(messages) <= MESSAGE_THRESHOLD:
        return {}
    llm = init_chat_model(
        "openai:qwen2.5-14b-instruct",
        base_url=os.environ.get("VLLM_UTILITY_URL", "http://vllm-utility:8000"),
        api_key="EMPTY",
        temperature=0,
    )
    text = "\n".join(
        f"{m.type}: {m.content}" for m in messages if hasattr(m, "content")
    )
    summary = await llm.ainvoke(
        [
            {"role": "system", "content": CONTEXT_SUMMARISER_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ]
    )
    deletes = [RemoveMessage(id=m.id) for m in messages if m.id is not None]
    return {"messages": [*deletes, summary]}
