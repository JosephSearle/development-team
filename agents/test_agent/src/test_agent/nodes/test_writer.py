"""test_writer node: generates a failing pytest file from a feature specification."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware
from dev_team_state.schema import TDDPhase
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware
from langchain.chat_models import init_chat_model

from test_agent.prompts.test_writer import TEST_WRITER_SYSTEM_PROMPT
from test_agent.schema import TestAgentState

VLLM_CODE_URL = os.getenv("VLLM_CODE_URL", "http://vllm-code:8000/v1")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/tmp/dev-team")


async def test_writer(state: TestAgentState) -> dict[str, Any]:
    """Generate a failing pytest file for the given feature spec."""
    workspace = Path(WORKSPACE_DIR) / state["subtask_id"]
    workspace.mkdir(parents=True, exist_ok=True)
    test_path = workspace / "tests" / "test_feature.py"

    model = init_chat_model(
        "openai:qwen2.5-coder-32b-instruct",
        base_url=VLLM_CODE_URL,
        api_key="EMPTY",
        temperature=0,
    )
    backend = FilesystemBackend(root_dir=str(workspace), virtual_mode=False)

    agent = create_deep_agent(
        model=model,
        tools=[],
        system_prompt=TEST_WRITER_SYSTEM_PROMPT,
        backend=backend,
        permissions=[
            FilesystemPermission(
                operations=["read", "write"],
                paths=[f"{workspace}/**"],
                mode="allow",
            ),
        ],
        middleware=[
            ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
            ToolRetryMiddleware(max_retries=2, retry_on=(TimeoutError, ConnectionError)),
            SummarizationMiddleware(model=model, backend=backend),
        ],
        skills=[str(Path(__file__).parent.parent / "skills")],
        name="test_writer",
    )

    user_message = (
        f"Feature spec: {state['feature_spec']}\n"
        f"Write the test file to: {test_path}"
    )
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config={"configurable": {"thread_id": state["subtask_id"]}},
    )

    if not test_path.exists():
        return {
            "status": "failed",
            "error": "Test writer did not produce a test file",
            "test_file_path": None,
        }

    test_code = test_path.read_text()

    try:
        compile(test_code, "<generated>", "exec")
    except SyntaxError:
        return {
            "status": "failed",
            "error": "Invalid Python syntax in generated test file",
            "test_file_path": None,
        }

    return {
        "test_code": test_code,
        "test_file_path": str(test_path),
        "tdd_phase": TDDPhase.RED,
        "messages": result.get("messages", []),
    }
