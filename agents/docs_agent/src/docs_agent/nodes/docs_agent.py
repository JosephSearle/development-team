"""Documentation Agent deepagents harness node."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware
from dev_team_mcp.registry import MCPRegistry
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage

from docs_agent.prompts.docs_agent import DOCS_AGENT_SYSTEM_PROMPT
from docs_agent.schema import DocsAgentState

VLLM_UTILITY_URL = os.getenv("VLLM_UTILITY_URL", "http://vllm-utility:8000/v1")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/tmp/dev-team")


def _build_user_message(state: DocsAgentState) -> str:
    workspace = Path(WORKSPACE_DIR) / state["subtask_id"]
    parts = [f"Task: {state['task_description']}"]
    parts.append(f"Write documentation files to: {workspace / 'docs'}")
    return "\n".join(parts)


async def docs_agent_node(state: DocsAgentState) -> dict[str, Any]:
    workspace = Path(WORKSPACE_DIR) / state["subtask_id"]
    workspace.mkdir(parents=True, exist_ok=True)
    docs_dir = workspace / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    mcp_client = MCPRegistry.build_client(["github"])
    tools = await mcp_client.get_tools()

    model = init_chat_model(
        "openai:qwen2.5-14b-instruct",
        base_url=VLLM_UTILITY_URL,
        api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
        temperature=0,
    )
    backend = FilesystemBackend(root_dir=str(workspace), virtual_mode=False)

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=DOCS_AGENT_SYSTEM_PROMPT,
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
        middleware=[
            ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
            ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
            SummarizationMiddleware(model=model, backend=backend),
        ],
        skills=[str(Path(__file__).parent.parent / "skills")],
        name="docs_agent",
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": _build_user_message(state)}]},
        config={"configurable": {"thread_id": state["subtask_id"]}},
    )

    messages = result.get("messages", [])
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)

    doc_files = sorted(docs_dir.rglob("*.md")) + sorted(docs_dir.rglob("*.rst"))
    file_paths_updated = [str(f) for f in doc_files]

    return {
        "file_paths_updated": file_paths_updated,
        "changelog_entry": "",
        "messages": [last_ai] if last_ai else [],
        "status": "completed",
        "error": None,
    }
