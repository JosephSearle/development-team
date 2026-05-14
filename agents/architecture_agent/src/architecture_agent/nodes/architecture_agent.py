"""Architecture Agent deepagents harness node."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from deepagents import AsyncSubAgent, FilesystemPermission, create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware
from dev_team_mcp.registry import MCPRegistry
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage

from architecture_agent.prompts.architecture_agent import ARCHITECTURE_AGENT_SYSTEM_PROMPT
from architecture_agent.schema import ArchitectureAgentState

VLLM_REASONING_URL = os.getenv("VLLM_REASONING_URL", "http://vllm-reasoning:8000/v1")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/tmp/dev-team")


def _build_user_message(state: ArchitectureAgentState) -> str:
    workspace = Path(WORKSPACE_DIR) / state["subtask_id"]
    parts = [f"Task: {state['task_description']}"]
    parts.append(f"Write ADR files to: {workspace / 'adrs'}")
    return "\n".join(parts)


async def architecture_agent_node(state: ArchitectureAgentState) -> dict[str, Any]:
    workspace = Path(WORKSPACE_DIR) / state["subtask_id"]
    workspace.mkdir(parents=True, exist_ok=True)
    adrs_dir = workspace / "adrs"
    adrs_dir.mkdir(parents=True, exist_ok=True)

    mcp_client = MCPRegistry.build_client(["context7", "github"])
    tools = await mcp_client.get_tools()

    model = init_chat_model(
        "openai:qwen3.5-72b-instruct",
        base_url=VLLM_REASONING_URL,
        api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
        temperature=0,
    )
    backend = FilesystemBackend(root_dir=str(workspace), virtual_mode=False)

    library_researcher = AsyncSubAgent(
        name="library_researcher",
        description=(
            "Fetches and evaluates library documentation from Context7 for architecture evaluation"
        ),
        graph_id="library_researcher",
    )

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=ARCHITECTURE_AGENT_SYSTEM_PROMPT,
        backend=backend,
        permissions=[
            FilesystemPermission(
                operations=["read", "write"],
                paths=[f"{workspace}/**"],
                mode="allow",
            ),
            FilesystemPermission(
                operations=["write"],
                paths=["/**/.env", "/**/secrets/**", "/**/*.key", "/**/*.pem"],
                mode="deny",
            ),
        ],
        subagents=[library_researcher],
        interrupt_on={"commit_file": True},
        middleware=[
            ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
            ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
            SummarizationMiddleware(model=model, backend=backend),
        ],
        skills=[str(Path(__file__).parent.parent / "skills")],
        name="architecture_agent",
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": _build_user_message(state)}]},
        config={"configurable": {"thread_id": state["subtask_id"]}},
    )

    messages = result.get("messages", [])
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)

    adr_files = sorted(adrs_dir.glob("*.md"))
    adr_path: str | None = str(adr_files[0]) if adr_files else None

    return {
        "adr_path": adr_path,
        "options_evaluated": [],
        "decision_rationale": (
            last_ai.content if last_ai and isinstance(last_ai.content, str) else ""
        ),
        "messages": [last_ai] if last_ai else [],
        "status": "completed",
        "error": None,
    }
