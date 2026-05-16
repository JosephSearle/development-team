"""Tests for the output_guardrail node."""

from __future__ import annotations

import pytest
from code_agent.nodes.output_guardrail import output_guardrail
from code_agent.schema import CodeAgentState


def _state_with_code(code: str) -> CodeAgentState:
    from dev_team_state.schema import TDDPhase

    return CodeAgentState(
        subtask_id="sub-001",
        feature_spec="spec",
        tdd_phase=TDDPhase.RED,
        test_file_path=None,
        test_results=None,
        written_code=code,
        implementation_file_path=None,
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
        iteration_count=0,
    )


class TestOutputGuardrailPass:
    def test_clean_code_passes(self) -> None:
        state = _state_with_code("def add(a, b):\n    return a + b\n")
        result = output_guardrail(state)
        assert result["guardrail_passed"] is True

    def test_returns_only_guardrail_passed_key_on_pass(self) -> None:
        state = _state_with_code("x = 1\n")
        result = output_guardrail(state)
        assert set(result.keys()) == {"guardrail_passed"}

    def test_no_code_passes(self, minimal_code_agent_state: CodeAgentState) -> None:
        state = {**minimal_code_agent_state, "written_code": None}
        result = output_guardrail(state)  # type: ignore[arg-type]
        assert result["guardrail_passed"] is True


class TestOutputGuardrailFail:
    @pytest.mark.parametrize("code", [
        'API_KEY = "sk-abc123xyz456def789ghi012"\n',
        'token = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.abc"\n',
        'SECRET = "my_super_secret_value_here"\n',
    ])
    def test_detects_secret_pattern(self, code: str) -> None:
        state = _state_with_code(code)
        result = output_guardrail(state)
        assert result["guardrail_passed"] is False

    def test_status_set_to_failed(self) -> None:
        state = _state_with_code('API_KEY = "sk-abc123xyzdef456gh789"\n')
        result = output_guardrail(state)
        assert result["status"] == "failed"

    def test_error_message_describes_pattern(self) -> None:
        state = _state_with_code('password = "supersecretpassword"\n')
        result = output_guardrail(state)
        assert "secret" in result["error"].lower()  # type: ignore[union-attr]
