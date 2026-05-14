"""Code Agent deepagents harness node."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware
from dev_team_mcp.registry import MCPRegistry
from dev_team_state.schema import TDDPhase
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware
from langchain.chat_models import init_chat_model

from code_agent.schema import CodeAgentState

VLLM_CODE_URL = os.getenv("VLLM_CODE_URL", "http://vllm-code:8000/v1")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/tmp/dev-team")
MAX_ITERATIONS = 5


def _build_system_prompt(state: CodeAgentState) -> str:
    if state["tdd_phase"] == TDDPhase.RED:
        return (
            "You are a TDD code agent in the RED→GREEN phase. "
            "Your task is to write the minimum Python implementation "
            "that makes the failing tests pass. "
            "Use read_file to read the test file, understand what is being tested, "
            "then use write_file to write the implementation. "
            "Use grep/glob to search the workspace for similar patterns. "
            "If the feature requires a named library, use Context7 tools for current docs. "
            "Never write tests. Never include secrets, credentials, API keys, or tokens."
        )
    return (
        "You are a TDD code agent in the REFACTOR phase. "
        "The tests are already passing. Improve code readability, type annotations, "
        "and structure without breaking any tests. "
        "Use read_file to inspect the current implementation, "
        "use grep/glob to understand conventions, "
        "then use write_file to write the improved version. "
        "Never include secrets, credentials, API keys, or tokens."
    )


def _build_user_message(state: CodeAgentState) -> str:
    parts = [f"Feature spec: {state['feature_spec']}"]
    if state["test_file_path"]:
        parts.append(f"Test file path: {state['test_file_path']}")
    test_results = state.get("test_results")
    if test_results and test_results["failure_details"]:
        failures = ", ".join(test_results["failure_details"])
        parts.append(f"Failing tests: {failures}")
    workspace = Path(WORKSPACE_DIR) / state["subtask_id"]
    parts.append(f"Write your implementation to: {workspace / 'src' / 'implementation.py'}")
    return "\n".join(parts)


async def code_agent_node(state: CodeAgentState) -> dict[str, Any]:
    if state["tdd_phase"] not in (TDDPhase.RED, TDDPhase.REFACTOR):
        return {}
    if state["iteration_count"] >= MAX_ITERATIONS:
        return {"status": "failed", "error": "Max iterations reached"}

    workspace = Path(WORKSPACE_DIR) / state["subtask_id"]
    workspace.mkdir(parents=True, exist_ok=True)
    impl_path = workspace / "src" / "implementation.py"

    mcp_client = MCPRegistry.build_client(["context7"])
    tools = await mcp_client.get_tools()

    model = init_chat_model(
        "openai:qwen2.5-coder-32b-instruct",
        base_url=VLLM_CODE_URL,
        api_key="EMPTY",
        temperature=0,
    )
    backend = FilesystemBackend(root_dir=str(workspace), virtual_mode=False)

    agent = create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=_build_system_prompt(state),
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
        name="code_agent",
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": _build_user_message(state)}]},
        config={"configurable": {"thread_id": state["subtask_id"]}},
    )

    written_code = impl_path.read_text() if impl_path.exists() else None
    return {
        "written_code": written_code,
        "implementation_file_path": str(impl_path),
        "iteration_count": state["iteration_count"] + 1,
        "messages": result.get("messages", []),
    }
