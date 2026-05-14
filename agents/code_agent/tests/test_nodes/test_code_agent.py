"""Tests for the code_agent node."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from code_agent.nodes.code_agent import MAX_ITERATIONS, code_agent_node
from code_agent.schema import CodeAgentState
from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware
from dev_team_state.schema import TDDPhase


class TestCodeAgentGate:
    async def test_returns_empty_when_setup_phase(
        self, minimal_code_agent_state: CodeAgentState
    ) -> None:
        state = {**minimal_code_agent_state, "tdd_phase": TDDPhase.SETUP}
        result = await code_agent_node(state)  # type: ignore[arg-type]
        assert result == {}

    async def test_returns_empty_when_green_phase(
        self, minimal_code_agent_state: CodeAgentState
    ) -> None:
        state = {**minimal_code_agent_state, "tdd_phase": TDDPhase.GREEN}
        result = await code_agent_node(state)  # type: ignore[arg-type]
        assert result == {}

    async def test_fails_when_max_iterations_reached(
        self, minimal_code_agent_state: CodeAgentState
    ) -> None:
        state = {**minimal_code_agent_state, "iteration_count": MAX_ITERATIONS}
        result = await code_agent_node(state)  # type: ignore[arg-type]
        assert result["status"] == "failed"
        assert "Max iterations" in result["error"]  # type: ignore[operator]


class TestCodeAgentDeepAgentConfig:
    async def test_calls_create_deep_agent_with_context7_tools(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await code_agent_node(minimal_code_agent_state)
        mock_deep_agent_code.assert_called_once()
        call_kwargs = mock_deep_agent_code.call_args.kwargs
        assert len(call_kwargs["tools"]) > 0

    async def test_filesystem_backend_configured(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await code_agent_node(minimal_code_agent_state)
        call_kwargs = mock_deep_agent_code.call_args.kwargs
        assert isinstance(call_kwargs["backend"], FilesystemBackend)

    async def test_summarization_middleware_in_stack(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await code_agent_node(minimal_code_agent_state)
        call_kwargs = mock_deep_agent_code.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_skills_path_configured(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await code_agent_node(minimal_code_agent_state)
        call_kwargs = mock_deep_agent_code.call_args.kwargs
        skills = call_kwargs["skills"]
        assert skills is not None
        assert len(skills) > 0

    async def test_filesystem_permissions_configured(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await code_agent_node(minimal_code_agent_state)
        call_kwargs = mock_deep_agent_code.call_args.kwargs
        assert call_kwargs["permissions"] is not None
        assert len(call_kwargs["permissions"]) > 0


class TestCodeAgentFileReadback:
    async def test_reads_written_code_from_disk(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        expected = "def add(a: int, b: int) -> int:\n    return a + b\n"
        impl_path = tmp_path / "sub-001" / "src" / "implementation.py"
        impl_path.parent.mkdir(parents=True)
        impl_path.write_text(expected)

        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await code_agent_node(minimal_code_agent_state)

        assert result["written_code"] == expected

    async def test_written_code_none_when_file_missing(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await code_agent_node(minimal_code_agent_state)
        assert result["written_code"] is None

    async def test_increments_iteration_count(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await code_agent_node(minimal_code_agent_state)
        assert result["iteration_count"] == minimal_code_agent_state["iteration_count"] + 1

    async def test_implementation_file_path_in_result(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await code_agent_node(minimal_code_agent_state)
        assert "implementation_file_path" in result
        assert "implementation.py" in result["implementation_file_path"]  # type: ignore[operator]


class TestCodeAgentPhasePrompts:
    async def test_red_phase_prompt_mentions_failing_tests(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await code_agent_node(minimal_code_agent_state)
        call_kwargs = mock_deep_agent_code.call_args.kwargs
        prompt = call_kwargs["system_prompt"]
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    async def test_refactor_phase_uses_different_prompt(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod

        red_state = minimal_code_agent_state
        refactor_state = {**minimal_code_agent_state, "tdd_phase": TDDPhase.REFACTOR}

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await code_agent_node(red_state)
        red_prompt = mock_deep_agent_code.call_args.kwargs["system_prompt"]

        mock_deep_agent_code.reset_mock()
        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await code_agent_node(refactor_state)  # type: ignore[arg-type]
        refactor_prompt = mock_deep_agent_code.call_args.kwargs["system_prompt"]

        assert red_prompt != refactor_prompt


class TestCodeAgentGraphIntegration:
    def test_graph_builds_without_error(self) -> None:
        from code_agent.graph import build_code_agent_graph

        graph = build_code_agent_graph()
        assert graph is not None

    def test_graph_has_code_agent_node(self) -> None:
        from code_agent.graph import build_code_agent_graph

        graph = build_code_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "code_agent_node" in node_names
        assert "output_guardrail" in node_names

    def test_graph_does_not_have_old_nodes(self) -> None:
        from code_agent.graph import build_code_agent_graph

        graph = build_code_agent_graph()
        node_names = set(graph.nodes.keys())
        assert "context7_client" not in node_names
        assert "codebase_search" not in node_names
        assert "code_writer" not in node_names
        assert "code_refactorer" not in node_names

    async def test_graph_routes_green_phase_to_end(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod
        from code_agent.graph import build_code_agent_graph

        green_state = {**minimal_code_agent_state, "tdd_phase": TDDPhase.GREEN}
        graph = build_code_agent_graph()
        config = {"configurable": {"thread_id": "test-green"}}
        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await graph.ainvoke(green_state, config=config)  # type: ignore[arg-type]
        mock_deep_agent_code.assert_not_called()
        assert result is not None

    async def test_graph_red_phase_calls_agent(
        self,
        mock_deep_agent_code: MagicMock,
        mock_context7_mcp: MagicMock,
        minimal_code_agent_state: CodeAgentState,
        tmp_path: Path,
    ) -> None:
        import code_agent.nodes.code_agent as mod
        from code_agent.graph import build_code_agent_graph

        graph = build_code_agent_graph()
        config = {"configurable": {"thread_id": "test-red"}}
        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await graph.ainvoke(minimal_code_agent_state, config=config)
        mock_deep_agent_code.assert_called_once()
