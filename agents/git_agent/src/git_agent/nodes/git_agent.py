"""Git Agent deepagents harness node."""

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

from git_agent.prompts.git_agent import GIT_AGENT_SYSTEM_PROMPT
from git_agent.schema import GitAgentState

VLLM_UTILITY_URL = os.getenv("VLLM_UTILITY_URL", "http://vllm-utility:8000/v1")


def _build_user_message(state: GitAgentState) -> str:
    parts = [f"Task: {state['task_description']}"]
    parts.append(f"Branch name: {state['branch_name']}")
    if state.get("commit_messages"):
        parts.append(f"Commits so far: {', '.join(state['commit_messages'])}")
    return "\n".join(parts)


async def git_agent_node(state: GitAgentState) -> dict[str, Any]:
    mcp_client = MCPRegistry.build_client(["github"])
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
        system_prompt=GIT_AGENT_SYSTEM_PROMPT,
        interrupt_on={"create_pull_request": True},
        middleware=[
            ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
            ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
            SummarizationMiddleware(model=model),
        ],
        skills=[str(Path(__file__).parent.parent / "skills")],
        name="git_agent",
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": _build_user_message(state)}]},
        config={"configurable": {"thread_id": state["subtask_id"]}},
    )

    messages = result.get("messages", [])
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)

    pr_url: str | None = state.get("pr_url")
    if last_ai:
        content = last_ai.content if isinstance(last_ai.content, str) else ""
        if "github.com" in content and "/pull/" in content:
            for token in content.split():
                if "github.com" in token and "/pull/" in token:
                    pr_url = token.strip(".,")
                    break

    return {
        "pr_url": pr_url,
        "messages": [last_ai] if last_ai else [],
        "status": "completed",
    }
