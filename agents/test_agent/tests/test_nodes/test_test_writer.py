"""Tests for the test_writer node."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware
from dev_team_state.schema import TDDPhase
from langchain_core.messages import AIMessage
from test_agent.nodes.test_writer import test_writer as _test_writer
from test_agent.schema import TestAgentState

_VALID_PYTEST_CODE = (
    "import pytest\n\n\ndef test_add():\n    from mymodule import add\n    assert add(1, 2) == 3\n"
)
_INVALID_PYTHON_CODE = "def test_broken(\n    assert True\n"


def _make_mock_deep_agent(tmp_path: Path, write_content: str | None) -> MagicMock:
    """Return a mock create_deep_agent that writes write_content to the expected test file."""
    test_path = tmp_path / "sub-001" / "tests" / "test_feature.py"

    def _side_effect(inputs: object, config: object = None) -> dict[str, object]:
        if write_content is not None:
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(write_content)
        return {"messages": [AIMessage(content="")]}

    mock_graph = MagicMock()
    mock_graph.ainvoke = AsyncMock(side_effect=_side_effect)
    return MagicMock(return_value=mock_graph)


@pytest.fixture()
def mock_deep_agent_writer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> MagicMock:
    import test_agent.nodes.test_writer as mod

    mock_create = _make_mock_deep_agent(tmp_path, _VALID_PYTEST_CODE)
    monkeypatch.setattr(mod, "create_deep_agent", mock_create)
    monkeypatch.setattr(mod, "WORKSPACE_DIR", str(tmp_path))
    return mock_create


@pytest.fixture()
def mock_deep_agent_invalid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> MagicMock:
    import test_agent.nodes.test_writer as mod

    mock_create = _make_mock_deep_agent(tmp_path, _INVALID_PYTHON_CODE)
    monkeypatch.setattr(mod, "create_deep_agent", mock_create)
    monkeypatch.setattr(mod, "WORKSPACE_DIR", str(tmp_path))
    return mock_create


@pytest.fixture()
def mock_deep_agent_no_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> MagicMock:
    import test_agent.nodes.test_writer as mod

    mock_create = _make_mock_deep_agent(tmp_path, None)
    monkeypatch.setattr(mod, "create_deep_agent", mock_create)
    monkeypatch.setattr(mod, "WORKSPACE_DIR", str(tmp_path))
    return mock_create


class TestTestWriterOutputShape:
    async def test_returns_test_code_as_string(
        self, mock_deep_agent_writer: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert isinstance(result["test_code"], str)
        assert len(result["test_code"]) > 0  # type: ignore[arg-type]

    async def test_sets_test_file_path(
        self, mock_deep_agent_writer: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert isinstance(result["test_file_path"], str)
        assert result["test_file_path"].endswith(".py")  # type: ignore[union-attr]

    async def test_sets_tdd_phase_to_red(
        self, mock_deep_agent_writer: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert result["tdd_phase"] == TDDPhase.RED

    async def test_returns_messages_list(
        self, mock_deep_agent_writer: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert isinstance(result["messages"], list)


class TestTestWriterDeepAgentConfig:
    async def test_filesystem_backend_configured(
        self, mock_deep_agent_writer: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        await _test_writer(minimal_test_agent_state)
        call_kwargs = mock_deep_agent_writer.call_args.kwargs
        assert isinstance(call_kwargs["backend"], FilesystemBackend)

    async def test_summarization_middleware_in_stack(
        self, mock_deep_agent_writer: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        await _test_writer(minimal_test_agent_state)
        call_kwargs = mock_deep_agent_writer.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_skills_path_configured(
        self, mock_deep_agent_writer: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        await _test_writer(minimal_test_agent_state)
        call_kwargs = mock_deep_agent_writer.call_args.kwargs
        skills = call_kwargs["skills"]
        assert skills is not None
        assert len(skills) > 0

    async def test_feature_spec_in_user_message(
        self, mock_deep_agent_writer: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        await _test_writer(minimal_test_agent_state)
        mock_deep_agent_writer.assert_called_once()


class TestTestWriterFileReadback:
    async def test_test_code_matches_file_content(
        self, mock_deep_agent_writer: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert result["test_code"] == _VALID_PYTEST_CODE

    async def test_no_file_written_sets_status_failed(
        self, mock_deep_agent_no_file: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert result["status"] == "failed"

    async def test_no_file_written_sets_error(
        self, mock_deep_agent_no_file: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert result["error"] is not None


class TestTestWriterInvalidPython:
    async def test_syntax_error_sets_status_failed(
        self, mock_deep_agent_invalid: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert result["status"] == "failed"

    async def test_syntax_error_sets_error_field(
        self, mock_deep_agent_invalid: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert result["error"] is not None
        assert "syntax" in result["error"].lower()  # type: ignore[union-attr]

    async def test_syntax_error_does_not_write_file_path(
        self, mock_deep_agent_invalid: MagicMock, minimal_test_agent_state: TestAgentState
    ) -> None:
        result = await _test_writer(minimal_test_agent_state)
        assert result.get("test_file_path") is None
