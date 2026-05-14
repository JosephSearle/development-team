"""output_guardrail node — deterministic regex check for secrets in generated code."""

from __future__ import annotations

import re
from typing import Any

from code_agent.schema import CodeAgentState

_SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r'(?i)(api_key|secret|password|token)\s*=\s*["\'][^"\']{8,}["\']'),
    re.compile(r"(?i)bearer\s+[a-z0-9_\-\.]{20,}"),
    re.compile(r"(?i)sk-[a-z0-9]{32,}"),
]


def output_guardrail(state: CodeAgentState) -> dict[str, Any]:
    written_code = state.get("written_code")
    if not written_code:
        return {"guardrail_passed": True}

    for pattern in _SECRET_PATTERNS:
        if pattern.search(written_code):
            return {
                "guardrail_passed": False,
                "status": "failed",
                "error": "Secret pattern detected in generated code — output rejected",
            }

    return {"guardrail_passed": True}
