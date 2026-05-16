"""reviewer node — LLM-based code review gated by scan_complete."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from dev_team_mcp.registry import MCPRegistry
from dev_team_state.schema import CodeReviewResult
from langchain.agents.middleware import (
    ModelRetryMiddleware,
    SummarizationMiddleware,
    ToolRetryMiddleware,
)
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage

from code_review_agent.prompts.reviewer import REVIEWER_SYSTEM_PROMPT
from code_review_agent.schema import CodeReviewAgentState

VLLM_REASONING_URL = os.getenv("VLLM_REASONING_URL", "http://vllm-reasoning:8000/v1")


def _build_prompt(state: CodeReviewAgentState) -> str:
    parts = [f"Feature spec: {state['feature_spec']}"]

    written_code = state.get("written_code") or ""
    parts.append(f"\nImplementation:\n```python\n{written_code}\n```")

    test_results = state.get("test_results")
    if test_results:
        parts.append(
            f"\nTest results: {test_results['passed']} passed, {test_results['failed']} failed, "
            f"exit_code={test_results['exit_code']}, "
            f"line_coverage={test_results.get('coverage_line_pct')}%"
        )

    return "\n".join(parts)


async def reviewer(state: CodeReviewAgentState) -> dict[str, Any]:
    if not state.get("scan_complete"):
        return {}

    mcp_client = MCPRegistry.build_client(["github"])
    tools = await mcp_client.get_tools()

    model = init_chat_model(
        "openai:qwen3.5-72b-instruct",
        base_url=VLLM_REASONING_URL,
        api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
        temperature=0,
    )

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=REVIEWER_SYSTEM_PROMPT,
        middleware=[
            ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
            ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
            SummarizationMiddleware(model=model),
        ],
        skills=[str(Path(__file__).parent.parent / "skills")],
        name="reviewer",
    )

    prompt = _build_prompt(state)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})

    messages = result.get("messages", [])
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
    content = last_ai.content if last_ai else ""
    raw_content = content if isinstance(content, str) else ""

    try:
        parsed = json.loads(raw_content)
        review_result = CodeReviewResult(
            approved=bool(parsed.get("approved", False)),
            reviewer_model=str(parsed.get("reviewer_model", "")),
            comments=list(parsed.get("comments", [])),
            blocking_issues=list(parsed.get("blocking_issues", [])),
            metadata=dict(parsed.get("metadata", {})),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return {
            "status": "failed",
            "error": "Reviewer returned malformed JSON",
            "messages": [last_ai] if last_ai else [],
        }

    status = "completed" if review_result["approved"] else "awaiting_approval"

    return {
        "review_result": review_result,
        "status": status,
        "messages": [last_ai] if last_ai else [],
    }
