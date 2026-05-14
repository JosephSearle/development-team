"""Tests for the architecture_agent node."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from architecture_agent.nodes.architecture_agent import architecture_agent_node
from architecture_agent.schema import ArchitectureAgentState
from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware


class TestArchitectureAgentDeepAgentConfig:
    async def test_calls_create_deep_agent(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await architecture_agent_node(minimal_architecture_agent_state)
        mock_deep_agent_arch.assert_called_once()

    async def test_context7_and_github_mcp_tools_wired(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await architecture_agent_node(minimal_architecture_agent_state)
        mock_mcp_arch.assert_called_once_with(["context7", "github"])

    async def test_filesystem_backend_configured(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await architecture_agent_node(minimal_architecture_agent_state)
        call_kwargs = mock_deep_agent_arch.call_args.kwargs
        assert isinstance(call_kwargs["backend"], FilesystemBackend)

    async def test_deepagents_summarization_middleware(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await architecture_agent_node(minimal_architecture_agent_state)
        call_kwargs = mock_deep_agent_arch.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_filesystem_permissions_configured(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await architecture_agent_node(minimal_architecture_agent_state)
        call_kwargs = mock_deep_agent_arch.call_args.kwargs
        assert call_kwargs.get("permissions") is not None
        assert len(call_kwargs["permissions"]) > 0

    async def test_library_researcher_subagent_wired(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await architecture_agent_node(minimal_architecture_agent_state)
        call_kwargs = mock_deep_agent_arch.call_args.kwargs
        subagents = call_kwargs.get("subagents", [])
        assert len(subagents) == 1
        assert subagents[0]["name"] == "library_researcher"

    async def test_interrupt_on_commit_file(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await architecture_agent_node(minimal_architecture_agent_state)
        call_kwargs = mock_deep_agent_arch.call_args.kwargs
        assert call_kwargs.get("interrupt_on") == {"commit_file": True}

    async def test_skills_path_set(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await architecture_agent_node(minimal_architecture_agent_state)
        call_kwargs = mock_deep_agent_arch.call_args.kwargs
        assert call_kwargs.get("skills") is not None
        assert len(call_kwargs["skills"]) > 0

    async def test_agent_name_is_architecture_agent(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await architecture_agent_node(minimal_architecture_agent_state)
        call_kwargs = mock_deep_agent_arch.call_args.kwargs
        assert call_kwargs.get("name") == "architecture_agent"


class TestArchitectureAgentFileReadback:
    async def test_reads_adr_from_disk(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        adr_content = "# 0007 — Adopt LangGraph\n\n**Status:** Proposed\n"
        adrs_dir = tmp_path / "sub-001" / "adrs"
        adrs_dir.mkdir(parents=True)
        (adrs_dir / "0007-adopt-langgraph.md").write_text(adr_content)

        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await architecture_agent_node(minimal_architecture_agent_state)

        assert result.get("adr_path") is not None
        assert "0007-adopt-langgraph.md" in result["adr_path"]  # type: ignore[operator]

    async def test_returns_none_adr_path_when_no_file_written(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await architecture_agent_node(minimal_architecture_agent_state)

        assert result.get("adr_path") is None

    async def test_returns_status_completed(
        self,
        mock_deep_agent_arch: MagicMock,
        mock_mcp_arch: MagicMock,
        minimal_architecture_agent_state: ArchitectureAgentState,
        tmp_path: Path,
    ) -> None:
        import architecture_agent.nodes.architecture_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await architecture_agent_node(minimal_architecture_agent_state)
        assert result.get("status") == "completed"
