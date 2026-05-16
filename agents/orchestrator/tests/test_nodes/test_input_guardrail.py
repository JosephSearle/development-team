"""TDD tests for the input_guardrail node."""

from __future__ import annotations

from typing import Any

import pytest
from dev_team_guardrail import GuardrailResult, GuardrailUnavailableError
from dev_team_state import OrchestratorState
from orchestrator.nodes.input_guardrail import input_guardrail


class TestInputGuardrailPass:
    async def test_sets_guardrail_passed_true_when_safe(
        self, mock_guardrail_pass: None, minimal_state: OrchestratorState
    ) -> None:
        result = await input_guardrail(minimal_state)
        assert result["guardrail_passed"] is True

    async def test_returns_only_guardrail_passed_key(
        self, mock_guardrail_pass: None, minimal_state: OrchestratorState
    ) -> None:
        result = await input_guardrail(minimal_state)
        assert set(result.keys()) == {"guardrail_passed"}

    async def test_screen_called_with_task_description(
        self, monkeypatch: pytest.MonkeyPatch, minimal_state: OrchestratorState
    ) -> None:
        captured: list[str] = []

        async def _screen(self: Any, text: str) -> GuardrailResult:
            captured.append(text)
            return GuardrailResult(passed=True, category=None)

        monkeypatch.setattr(
            "orchestrator.nodes.input_guardrail.GuardrailClient.screen", _screen
        )
        await input_guardrail(minimal_state)
        assert captured == [minimal_state["task_description"]]


class TestInputGuardrailFail:
    async def test_sets_guardrail_passed_false_when_unsafe(
        self, mock_guardrail_fail: None, minimal_state: OrchestratorState
    ) -> None:
        result = await input_guardrail(minimal_state)
        assert result["guardrail_passed"] is False


class TestInputGuardrailUnavailable:
    async def test_guardrail_unavailable_error_propagates(
        self, monkeypatch: pytest.MonkeyPatch, minimal_state: OrchestratorState
    ) -> None:
        async def _raise(self: Any, text: str) -> GuardrailResult:
            raise GuardrailUnavailableError("endpoint unreachable")

        monkeypatch.setattr(
            "orchestrator.nodes.input_guardrail.GuardrailClient.screen", _raise
        )
        with pytest.raises(GuardrailUnavailableError):
            await input_guardrail(minimal_state)
