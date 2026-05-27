from __future__ import annotations

from cloakbrowser_mcp.config import Settings
from cloakbrowser_mcp.server import create_mcp_server
from cloakbrowser_mcp.tools import TOOL_DEFINITIONS


def test_tool_definitions_are_unique():
    names = [item["name"] for item in TOOL_DEFINITIONS]
    assert len(names) == len(set(names))
    assert "browser_launch" in names
    assert "cloakbrowser_healthcheck" in names
    assert "browser_start_cdp" in names


def test_server_can_be_created():
    server = create_mcp_server(Settings())
    assert server.name == "cloakbrowser-mcp"


async def test_mcp_can_list_tool_schemas():
    server = create_mcp_server(Settings())
    tools = await server.list_tools()
    names = {tool.name for tool in tools}
    assert len(tools) == len(TOOL_DEFINITIONS)
    assert "browser_launch" in names
    launch_schema = next(tool.inputSchema for tool in tools if tool.name == "browser_launch")
    assert "properties" in launch_schema
