"""Tests for the security agent output_guardrail node."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from security_agent.nodes.output_guardrail import output_guardrail
from security_agent.schema import SecurityAgentState


def _make_state(sast_findings: list[str] | None = None) -> SecurityAgentState:
    return SecurityAgentState(
        subtask_id="sub-001",
        diff_content="+def add(a, b):\n+    return a + b",
        secrets_detected=False,
        scan_complete=True,
        sast_findings=sast_findings or [],
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
    )


@pytest.fixture()
def mock_guardrail_pass(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_result = MagicMock()
    mock_result.passed = True
    mock_result.category = None
    mock_client = MagicMock()
    mock_client.screen = AsyncMock(return_value=mock_result)
    mock_cls = MagicMock(return_value=mock_client)
    monkeypatch.setattr("security_agent.nodes.output_guardrail.GuardrailClient", mock_cls)
    return mock_cls


@pytest.fixture()
def mock_guardrail_fail(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_result = MagicMock()
    mock_result.passed = False
    mock_result.category = "S7"
    mock_client = MagicMock()
    mock_client.screen = AsyncMock(return_value=mock_result)
    mock_cls = MagicMock(return_value=mock_client)
    monkeypatch.setattr("security_agent.nodes.output_guardrail.GuardrailClient", mock_cls)
    return mock_cls


class TestOutputGuardrail:
    async def test_sets_guardrail_passed_true_on_clean(
        self, mock_guardrail_pass: MagicMock
    ) -> None:
        result = await output_guardrail(_make_state())
        assert result["guardrail_passed"] is True

    async def test_sets_guardrail_passed_false_on_violation(
        self, mock_guardrail_fail: MagicMock
    ) -> None:
        result = await output_guardrail(_make_state())
        assert result["guardrail_passed"] is False

    async def test_is_async(self) -> None:
        import inspect

        assert inspect.iscoroutinefunction(output_guardrail)
