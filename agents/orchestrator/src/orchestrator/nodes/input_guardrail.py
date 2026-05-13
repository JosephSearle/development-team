from __future__ import annotations

import os

from dev_team_guardrail import GuardrailClient
from dev_team_state import OrchestratorState


async def input_guardrail(state: OrchestratorState) -> dict[str, bool]:
    client = GuardrailClient(
        endpoint=os.environ.get("GUARDRAIL_URL", "http://llama-guard:8080"),
    )
    result = await client.screen(state["task_description"])
    return {"guardrail_passed": result.passed}
