from __future__ import annotations

import os
from typing import ClassVar

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection

_KNOWN_SERVERS: set[str] = {
    "github",
    "jira",
    "context7",
    "sonarqube",
    "jenkins",
    "slack",
}


class MCPRegistry:
    SERVERS: ClassVar[set[str]] = _KNOWN_SERVERS

    @classmethod
    def build_client(cls, server_names: list[str]) -> MultiServerMCPClient:
        if not server_names:
            return MultiServerMCPClient({})
        unknown = set(server_names) - cls.SERVERS
        if unknown:
            raise ValueError(f"Unknown MCP servers: {unknown}")

        connections: dict[str, StreamableHttpConnection] = {}
        for name in server_names:
            env_key = f"MCP_{name.upper()}_URL"
            url = os.environ.get(env_key, f"http://{name}-mcp:8080/mcp")
            connections[name] = StreamableHttpConnection(
                transport="streamable_http",
                url=url,
            )

        return MultiServerMCPClient(connections)  # type: ignore[arg-type]

    @classmethod
    async def get_tools(cls, server_name: str) -> list[BaseTool]:
        client = cls.build_client([server_name])
        return await client.get_tools(server_name=server_name)
