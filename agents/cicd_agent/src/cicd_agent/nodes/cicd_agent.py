"""CI/CD Agent deepagents harness node."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from dev_team_mcp.registry import MCPRegistry
from langchain.agents.middleware import (
    ModelRetryMiddleware,
    SummarizationMiddleware,
    ToolRetryMiddleware,
)
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage

from cicd_agent.prompts.cicd_agent import CICD_AGENT_SYSTEM_PROMPT
from cicd_agent.schema import CICDAgentState

VLLM_UTILITY_URL = os.getenv("VLLM_UTILITY_URL", "http://vllm-utility:8000/v1")


def _build_user_message(state: CICDAgentState) -> str:
    parts = [f"Task: {state['task_description']}"]
    if state.get("pipeline_type"):
        parts.append(f"Pipeline type: {state['pipeline_type']}")
    if state.get("deployment_env"):
        parts.append(f"Deployment environment: {state['deployment_env']}")
    return "\n".join(parts)


async def cicd_agent_node(state: CICDAgentState) -> dict[str, Any]:
    mcp_client = MCPRegistry.build_client(["jenkins", "github"])
    tools = await mcp_client.get_tools()

    model = init_chat_model(
        "openai:qwen2.5-14b-instruct",
        base_url=VLLM_UTILITY_URL,
        api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
        temperature=0,
    )

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=CICD_AGENT_SYSTEM_PROMPT,
        interrupt_on={"trigger_production_deploy": True},
        middleware=[
            ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
            ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
            SummarizationMiddleware(model=model),
        ],
        skills=[str(Path(__file__).parent.parent / "skills")],
        name="cicd_agent",
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": _build_user_message(state)}]},
        config={"configurable": {"thread_id": state["subtask_id"]}},
    )

    messages = result.get("messages", [])
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)

    return {
        "messages": [last_ai] if last_ai else [],
        "status": "completed",
    }
