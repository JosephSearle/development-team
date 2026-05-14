"""Tests for the infrastructure_agent node."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from deepagents.backends import FilesystemBackend
from deepagents.middleware import SummarizationMiddleware
from infrastructure_agent.nodes.infrastructure_agent import infrastructure_agent_node
from infrastructure_agent.schema import InfrastructureAgentState


class TestInfrastructureAgentDeepAgentConfig:
    async def test_calls_create_deep_agent(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await infrastructure_agent_node(minimal_infra_agent_state)
        mock_deep_agent_infra.assert_called_once()

    async def test_github_mcp_tools_wired(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await infrastructure_agent_node(minimal_infra_agent_state)
        mock_github_mcp_infra.assert_called_once_with(["github"])

    async def test_filesystem_backend_configured(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await infrastructure_agent_node(minimal_infra_agent_state)
        call_kwargs = mock_deep_agent_infra.call_args.kwargs
        assert isinstance(call_kwargs["backend"], FilesystemBackend)

    async def test_deepagents_summarization_middleware(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await infrastructure_agent_node(minimal_infra_agent_state)
        call_kwargs = mock_deep_agent_infra.call_args.kwargs
        middleware_types = [type(m) for m in call_kwargs["middleware"]]
        assert SummarizationMiddleware in middleware_types

    async def test_filesystem_permissions_configured(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await infrastructure_agent_node(minimal_infra_agent_state)
        call_kwargs = mock_deep_agent_infra.call_args.kwargs
        assert call_kwargs.get("permissions") is not None
        assert len(call_kwargs["permissions"]) > 0

    async def test_skills_path_set(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await infrastructure_agent_node(minimal_infra_agent_state)
        call_kwargs = mock_deep_agent_infra.call_args.kwargs
        assert call_kwargs.get("skills") is not None
        assert len(call_kwargs["skills"]) > 0

    async def test_agent_name_is_infrastructure_agent(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            await infrastructure_agent_node(minimal_infra_agent_state)
        call_kwargs = mock_deep_agent_infra.call_args.kwargs
        assert call_kwargs.get("name") == "infrastructure_agent"


class TestInfrastructureAgentFileReadback:
    async def test_reads_staged_manifest_from_disk(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        manifest_content = "apiVersion: apps/v1\nkind: Deployment\n"
        manifest_dir = tmp_path / "sub-001" / "manifests"
        manifest_dir.mkdir(parents=True)
        manifest_file = manifest_dir / "deployment.yaml"
        manifest_file.write_text(manifest_content)

        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await infrastructure_agent_node(minimal_infra_agent_state)

        assert result.get("manifests") is not None
        assert len(result["manifests"]) > 0  # type: ignore[arg-type]
        assert "apiVersion" in result["manifests"][0]  # type: ignore[index]

    async def test_returns_empty_manifests_when_none_written(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await infrastructure_agent_node(minimal_infra_agent_state)

        assert result.get("manifests") == []
        assert result.get("manifest_paths") == []

    async def test_returns_status_completed(
        self,
        mock_deep_agent_infra: MagicMock,
        mock_github_mcp_infra: MagicMock,
        minimal_infra_agent_state: InfrastructureAgentState,
        tmp_path: Path,
    ) -> None:
        import infrastructure_agent.nodes.infrastructure_agent as mod

        with patch.object(mod, "WORKSPACE_DIR", str(tmp_path)):
            result = await infrastructure_agent_node(minimal_infra_agent_state)
        assert result.get("status") == "completed"
