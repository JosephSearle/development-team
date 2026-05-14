"""Incident Response Agent deepagents harness node."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from deepagents import AsyncSubAgent, create_deep_agent
from dev_team_mcp.registry import MCPRegistry
from langchain.agents.middleware import (
    ModelRetryMiddleware,
    SummarizationMiddleware,
    ToolRetryMiddleware,
)
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage

from incident_response_agent.prompts.incident_response_agent import (
    INCIDENT_RESPONSE_AGENT_SYSTEM_PROMPT,
)
from incident_response_agent.schema import IncidentResponseAgentState

VLLM_REASONING_URL = os.getenv("VLLM_REASONING_URL", "http://vllm-reasoning:8000/v1")

_JIRA_URL_RE = re.compile(r"https?://[^\s/]+/browse/[A-Z]+-\d+")


def _build_user_message(state: IncidentResponseAgentState) -> str:
    parts = [f"Task: {state['task_description']}"]
    if state.get("alert_context"):
        parts.append(f"Alert context: {state['alert_context']}")
    return "\n".join(parts)


def _extract_jira_url(content: str) -> str | None:
    match = _JIRA_URL_RE.search(content)
    return match.group(0) if match else None


async def incident_response_agent_node(state: IncidentResponseAgentState) -> dict[str, Any]:
    mcp_client = MCPRegistry.build_client(["github", "jira", "kubernetes"])
    tools = await mcp_client.get_tools()

    model = init_chat_model(
        "openai:qwen3.5-72b-instruct",
        base_url=VLLM_REASONING_URL,
        api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
        temperature=0,
    )

    log_analyzer = AsyncSubAgent(
        name="log_analyzer",
        description="Analyse Kubernetes pod logs for error patterns",
        graph_id="log_analyzer",
    )
    metrics_analyzer = AsyncSubAgent(
        name="metrics_analyzer",
        description="Query Prometheus metrics for anomaly detection",
        graph_id="metrics_analyzer",
    )

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=INCIDENT_RESPONSE_AGENT_SYSTEM_PROMPT,
        subagents=[log_analyzer, metrics_analyzer],
        interrupt_on={"create_jira_issue": True},
        middleware=[
            ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
            ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
            SummarizationMiddleware(model=model),
        ],
        skills=[str(Path(__file__).parent.parent / "skills")],
        name="incident_response_agent",
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": _build_user_message(state)}]},
        config={"configurable": {"thread_id": state["subtask_id"]}},
    )

    messages = result.get("messages", [])
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)

    jira_issue_url: str | None = None
    if last_ai and isinstance(last_ai.content, str):
        jira_issue_url = _extract_jira_url(last_ai.content)

    return {
        "jira_issue_url": jira_issue_url,
        "root_cause": last_ai.content if last_ai and isinstance(last_ai.content, str) else "",
        "remediation_steps": [],
        "runbook_path": None,
        "messages": [last_ai] if last_ai else [],
        "status": "completed",
        "error": None,
    }
