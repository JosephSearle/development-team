"""Tests for the docs_agent node."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware
from docs_agent.nodes.docs_agent import docs_agent_node
from docs_agent.schema import DocsAgentState


class TestDocsAgentDeepAgentConfig:
    async def test_calls_create_deep_agent(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await docs_agent_node(minimal_docs_agent_state)
        mock_deep_agent_docs.assert_called_once()

    async def test_github_mcp_tools_wired(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await docs_agent_node(minimal_docs_agent_state)
        mock_github_mcp_docs.assert_called_once_with(["github"])

    async def test_filesystem_backend_configured(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await docs_agent_node(minimal_docs_agent_state)
        call_kwargs = mock_deep_agent_docs.call_args.kwargs
        assert isinstance(call_kwargs["backend"], FilesystemBackend)

    async def test_deepagents_summarization_middleware(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await docs_agent_node(minimal_docs_agent_state)
        call_kwargs = mock_deep_agent_docs.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_filesystem_permissions_configured(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await docs_agent_node(minimal_docs_agent_state)
        call_kwargs = mock_deep_agent_docs.call_args.kwargs
        assert call_kwargs.get("permissions") is not None
        assert len(call_kwargs["permissions"]) > 0

    async def test_no_subagents(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await docs_agent_node(minimal_docs_agent_state)
        call_kwargs = mock_deep_agent_docs.call_args.kwargs
        assert call_kwargs.get("subagents") is None

    async def test_no_interrupt_on(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await docs_agent_node(minimal_docs_agent_state)
        call_kwargs = mock_deep_agent_docs.call_args.kwargs
        assert call_kwargs.get("interrupt_on") is None

    async def test_skills_path_set(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await docs_agent_node(minimal_docs_agent_state)
        call_kwargs = mock_deep_agent_docs.call_args.kwargs
        assert call_kwargs.get("skills") is not None
        assert len(call_kwargs["skills"]) > 0

    async def test_agent_name_is_docs_agent(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await docs_agent_node(minimal_docs_agent_state)
        call_kwargs = mock_deep_agent_docs.call_args.kwargs
        assert call_kwargs.get("name") == "docs_agent"


class TestDocsAgentFileReadback:
    async def test_reads_doc_files_from_disk(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        docs_dir = tmp_path / "sub-001" / "docs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "README.md").write_text("# Auth Service\n")

        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await docs_agent_node(minimal_docs_agent_state)

        assert result.get("file_paths_updated") is not None
        assert len(result["file_paths_updated"]) > 0  # type: ignore[arg-type]

    async def test_returns_empty_list_when_no_docs_written(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await docs_agent_node(minimal_docs_agent_state)

        assert result.get("file_paths_updated") == []

    async def test_returns_status_completed(
        self,
        mock_deep_agent_docs: MagicMock,
        mock_github_mcp_docs: MagicMock,
        minimal_docs_agent_state: DocsAgentState,
        tmp_path: Path,
    ) -> None:
        import docs_agent.nodes.docs_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await docs_agent_node(minimal_docs_agent_state)
        assert result.get("status") == "completed"
