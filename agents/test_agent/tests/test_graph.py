"""Tests for the Test Agent full graph."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from dev_team_state.schema import TDDPhase
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from test_agent.graph import build_test_agent_graph
from test_agent.schema import TestAgentState

_VALID_PYTEST_CODE = (
    "import pytest\n\n\ndef test_add():\n    from mymodule import add\n    assert add(1, 2) == 3\n"
)
_INVALID_PYTHON_CODE = "def test_broken(\n    assert True"


def _initial_state() -> TestAgentState:
    return TestAgentState(
        subtask_id="sub-001",
        feature_spec="Implement an add(a, b) function",
        tdd_phase=TDDPhase.SETUP,
        test_file_path=None,
        test_code=None,
        test_results=None,
        run_count=0,
        flaky_test_ids=[],
        guardrail_passed=True,
        messages=[],
        status="in_progress",
        error=None,
    )


def _make_failing_report() -> str:
    return json.dumps({
        "exitcode": 1,
        "summary": {"failed": 2, "passed": 0, "error": 0},
        "duration": 0.5,
        "tests": [{"nodeid": "test_add", "outcome": "failed"}],
        "totals": {"percent_covered": 85.0, "covered_branches": 72, "num_branches": 100},
    })


def _make_consistent_run_result(exit_code: int = 1) -> tuple[int, str]:
    return (exit_code, _make_failing_report())


def _make_writer_mock(tmp_path: Path, content: str | None) -> MagicMock:
    test_path = tmp_path / "sub-001" / "tests" / "test_feature.py"

    def _side_effect(inputs: object, config: object = None) -> dict[str, object]:
        if content is not None:
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(content)
        return {"messages": [AIMessage(content="")]}

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=_side_effect)
    return MagicMock(return_value=mock_graph)


@pytest.fixture()
def mock_deep_agent_valid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> MagicMock:
    import test_agent.nodes.test_writer as mod

    mock_create = _make_writer_mock(tmp_path, _VALID_PYTEST_CODE)
    monkeypatch.setattr(mod, "create_deep_agent", mock_create)
    monkeypatch.setattr(mod, "WORKSPACE_DIR", str(tmp_path))
    return mock_create


@pytest.fixture()
def mock_deep_agent_invalid_syntax(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> MagicMock:
    import test_agent.nodes.test_writer as mod

    mock_create = _make_writer_mock(tmp_path, _INVALID_PYTHON_CODE)
    monkeypatch.setattr(mod, "create_deep_agent", mock_create)
    monkeypatch.setattr(mod, "WORKSPACE_DIR", str(tmp_path))
    return mock_create


@pytest.fixture()
def mock_pytest_failing_then_consistent(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """First run fails (RED confirmed), subsequent flake runs also fail consistently."""
    mock = AsyncMock(return_value=_make_consistent_run_result(1))
    monkeypatch.setattr("test_agent.nodes.test_runner._run_pytest", mock)
    monkeypatch.setattr("test_agent.nodes.flake_detector._run_pytest", mock)
    return mock


class TestTestAgentGraphSmoke:
    async def test_graph_completes_red_phase(
        self,
        mock_deep_agent_valid: MagicMock,
        mock_pytest_failing_then_consistent: AsyncMock,
    ) -> None:
        graph = build_test_agent_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "smoke-1"}}
        result = await graph.ainvoke(_initial_state(), config=config)
        assert result["tdd_phase"] == TDDPhase.GREEN
        assert result["status"] == "completed"

    async def test_graph_sets_test_file_path(
        self,
        mock_deep_agent_valid: MagicMock,
        mock_pytest_failing_then_consistent: AsyncMock,
    ) -> None:
        graph = build_test_agent_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "smoke-2"}}
        result = await graph.ainvoke(_initial_state(), config=config)
        assert result["test_file_path"] is not None
        assert result["test_file_path"].endswith(".py")  # type: ignore[union-attr]

    async def test_graph_fails_gracefully_on_syntax_error(
        self, mock_deep_agent_invalid_syntax: MagicMock
    ) -> None:
        graph = build_test_agent_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "syntax-err-1"}}
        result = await graph.ainvoke(_initial_state(), config=config)
        assert result["status"] == "failed"
        assert result["error"] is not None


class TestTestAgentGraphNodeOrder:
    async def test_flake_detector_runs_after_coverage_passes(
        self,
        mock_deep_agent_valid: MagicMock,
        mock_pytest_failing_then_consistent: AsyncMock,
    ) -> None:
        graph = build_test_agent_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "order-1"}, "stream_mode": "updates"}
        node_names: list[str] = []
        async for chunk in graph.astream(_initial_state(), config=config, stream_mode="updates"):
            node_names.extend(chunk.keys())
        assert "flake_detector" in node_names
        assert node_names.index("coverage_checker") < node_names.index("flake_detector")
