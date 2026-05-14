"""Secrets scanner — synchronous deterministic node, no LLM."""

from __future__ import annotations

import re
from typing import Any

from security_agent.schema import SecurityAgentState

_AWS_SECRET_RE = re.compile(
    r"(?i)aws.{0,20}secret.{0,20}[=:'" r'"\s][0-9a-zA-Z/+]{40}'
)
_API_KEY_RE = re.compile(
    r"""(?i)(api.?key|secret.?key|auth.?token)['"\s=:]+['"][a-zA-Z0-9_-]{20,}['"]"""
)

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS Access Key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS Secret Access Key", _AWS_SECRET_RE),
    ("Private key header", re.compile(r"-----BEGIN\s+(RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY")),
    ("Generic API key", _API_KEY_RE),
    ("Generic bearer token", re.compile(r"(?i)bearer\s+[a-zA-Z0-9_.~-]{20,}")),
]


def secrets_scanner(state: SecurityAgentState) -> dict[str, Any]:
    diff = state.get("diff_content") or ""

    for label, pattern in _SECRET_PATTERNS:
        if pattern.search(diff):
            return {
                "secrets_detected": True,
                "status": "failed",
                "error": f"Secret detected in diff: {label}",
            }

    return {"secrets_detected": False}
