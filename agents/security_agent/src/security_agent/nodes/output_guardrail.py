"""Output guardrail — screens SAST findings through Llama-Guard-3-8B."""

from __future__ import annotations

import os
from typing import Any

from dev_team_guardrail.client import GuardrailClient

from security_agent.schema import SecurityAgentState

GUARDRAIL_URL = os.getenv("GUARDRAIL_URL", "http://llama-guard:8000")


async def output_guardrail(state: SecurityAgentState) -> dict[str, Any]:
    findings_text = "\n".join(state.get("sast_findings") or []) or "No findings."
    client = GuardrailClient(endpoint=GUARDRAIL_URL)
    result = await client.screen(findings_text)
    return {"guardrail_passed": result.passed}
