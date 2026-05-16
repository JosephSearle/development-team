"""Dependency Agent deepagents harness node."""

from __future__ import annotations

import os
import re
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

from dependency_agent.prompts.dependency_agent import DEPENDENCY_AGENT_SYSTEM_PROMPT
from dependency_agent.schema import DependencyAgentState

VLLM_UTILITY_URL = os.getenv("VLLM_UTILITY_URL", "http://vllm-utility:8000/v1")

_PR_URL_RE = re.compile(r"https://github\.com/[^\s/]+/[^\s/]+/pull/\d+")


def _build_user_message(state: DependencyAgentState) -> str:
    parts = [f"Task: {state['task_description']}"]
    return "\n".join(parts)


def _extract_pr_urls(content: str) -> list[str]:
    return _PR_URL_RE.findall(content)


async def dependency_agent_node(state: DependencyAgentState) -> dict[str, Any]:
    mcp_client = MCPRegistry.build_client(["github", "sonarqube"])
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
        system_prompt=DEPENDENCY_AGENT_SYSTEM_PROMPT,
        middleware=[
            ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
            ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
            SummarizationMiddleware(model=model),
        ],
        skills=[str(Path(__file__).parent.parent / "skills")],
        name="dependency_agent",
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": _build_user_message(state)}]},
        config={"configurable": {"thread_id": state["subtask_id"]}},
    )

    messages = result.get("messages", [])
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)

    pr_urls: list[str] = []
    if last_ai and isinstance(last_ai.content, str):
        pr_urls = _extract_pr_urls(last_ai.content)

    return {
        "pr_urls": pr_urls,
        "dependencies_scanned": [],
        "vulnerabilities_found": [],
        "upgrades_proposed": [],
        "messages": [last_ai] if last_ai else [],
        "status": "completed",
        "error": None,
    }
