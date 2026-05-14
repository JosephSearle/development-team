"""Tests for the secrets_scanner node."""

from __future__ import annotations

from security_agent.nodes.secrets_scanner import secrets_scanner
from security_agent.schema import SecurityAgentState


def _make_state(diff_content: str | None = None) -> SecurityAgentState:
    return SecurityAgentState(
        subtask_id="sub-001",
        diff_content=diff_content,
        secrets_detected=False,
        scan_complete=False,
        sast_findings=[],
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
    )


class TestSecretsScanner:
    def test_clean_diff_passes(self) -> None:
        state = _make_state("+def add(a, b):\n+    return a + b")
        result = secrets_scanner(state)
        assert result["secrets_detected"] is False
        assert "status" not in result or result.get("status") != "failed"

    def test_empty_diff_passes(self) -> None:
        state = _make_state("")
        result = secrets_scanner(state)
        assert result["secrets_detected"] is False

    def test_none_diff_passes(self) -> None:
        state = _make_state(None)
        result = secrets_scanner(state)
        assert result["secrets_detected"] is False

    def test_aws_access_key_detected(self) -> None:
        state = _make_state("+AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
        result = secrets_scanner(state)
        assert result["secrets_detected"] is True
        assert result.get("status") == "failed"
        assert result.get("error")

    def test_aws_secret_key_detected(self) -> None:
        state = _make_state("+AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
        result = secrets_scanner(state)
        assert result["secrets_detected"] is True
        assert result.get("status") == "failed"

    def test_private_key_header_detected(self) -> None:
        state = _make_state("+-----BEGIN RSA PRIVATE KEY-----\n+MIIE...")
        result = secrets_scanner(state)
        assert result["secrets_detected"] is True
        assert result.get("status") == "failed"

    def test_generic_api_key_pattern_detected(self) -> None:
        state = _make_state('+api_key = "sk-abc123def456ghi789jkl012mno345pqr678"')
        result = secrets_scanner(state)
        assert result["secrets_detected"] is True
        assert result.get("status") == "failed"

    def test_scanner_is_synchronous(self) -> None:
        import inspect

        assert not inspect.iscoroutinefunction(secrets_scanner)
