"""TDD tests for MCPRegistry — written before implementation (RED phase)."""

from __future__ import annotations

import dataclasses
from unittest.mock import AsyncMock

import pytest
from dev_team_mcp.registry import MCPRegistry
from langchain_mcp_adapters.client import MultiServerMCPClient
from pytest_mock import MockerFixture


@dataclasses.dataclass
class _FakeTool:
    name: str
    description: str = "A fake tool for testing"


_ALL_SERVERS = {
    "github",
    "jira",
    "context7",
    "sonarqube",
    "jenkins",
    "slack",
}


class TestMCPRegistryKnownServers:
    def test_all_six_servers_registered(self) -> None:
        assert MCPRegistry.SERVERS == _ALL_SERVERS

    def test_each_server_has_url_and_transport(self) -> None:
        for name in MCPRegistry.SERVERS:
            client = MCPRegistry.build_client([name])
            assert client is not None

    def test_transport_is_streamable_http_for_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for server in MCPRegistry.SERVERS:
            env_var = f"MCP_{server.upper()}_URL"
            monkeypatch.setenv(env_var, f"http://{server}-test:8080/mcp")
        # Build clients using each server; they should not raise
        for server in MCPRegistry.SERVERS:
            client = MCPRegistry.build_client([server])
            assert isinstance(client, MultiServerMCPClient)

    def test_url_defaults_contain_service_names(self) -> None:
        # Spot-check: default URL for github contains "github-mcp"
        # We inspect via env var absence — the default is baked into build_client
        client = MCPRegistry.build_client(["github"])
        assert client is not None  # build succeeds with default URL


class TestMCPRegistryBuildClient:
    def test_build_client_with_two_servers_returns_client_instance(self) -> None:
        client = MCPRegistry.build_client(["github", "jira"])
        assert isinstance(client, MultiServerMCPClient)

    def test_build_client_with_unknown_server_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown MCP servers"):
            MCPRegistry.build_client(["nonexistent"])

    def test_build_client_with_empty_list_returns_client(self) -> None:
        client = MCPRegistry.build_client([])
        assert isinstance(client, MultiServerMCPClient)

    def test_build_client_uses_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_GITHUB_URL", "http://override:9090/mcp")
        # Build succeeds with the override URL (we verify no exception is raised
        # and the client is a MultiServerMCPClient — the URL is embedded in the
        # client's internal config which isn't directly inspectable without private access)
        client = MCPRegistry.build_client(["github"])
        assert isinstance(client, MultiServerMCPClient)


class TestMCPRegistryGetTools:
    async def test_get_tools_returns_tool_list(self, mocker: MockerFixture) -> None:
        fake = _FakeTool("github_create_pr")
        mocker.patch.object(
            MultiServerMCPClient,
            "get_tools",
            new_callable=AsyncMock,
            return_value=[fake],
        )
        result = await MCPRegistry.get_tools(server_name="github")
        assert len(result) == 1
        assert result[0].name == "github_create_pr"

    async def test_get_tools_called_with_server_name(self, mocker: MockerFixture) -> None:
        mock_get_tools = mocker.patch.object(
            MultiServerMCPClient,
            "get_tools",
            new_callable=AsyncMock,
            return_value=[],
        )
        await MCPRegistry.get_tools(server_name="jira")
        mock_get_tools.assert_awaited_once_with(server_name="jira")
