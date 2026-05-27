"""FastMCP 服务入口。"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .browser import BrowserSessionManager
from .config import Settings, load_settings
from .tools import register_tools

SERVER_INSTRUCTIONS = """
CloakBrowser MCP exposes CloakBrowser stealth Chromium through MCP tools.
Recommended flow for AI agents:
1. call cloakbrowser_healthcheck;
2. call browser_launch with explicit task settings when needed;
3. use browser_navigate and page action tools;
4. call browser_close after work is done.
All tools are enabled by default and return structured JSON.
"""


def create_mcp_server(settings: Settings | None = None) -> FastMCP:
    settings = settings or load_settings()
    mcp = FastMCP(
        settings.server.name,
        instructions=SERVER_INSTRUCTIONS,
        stateless_http=settings.server.stateless_http,
        json_response=settings.server.json_response,
        streamable_http_path=settings.server.path,
    )
    mcp.settings.host = settings.server.host
    mcp.settings.port = settings.server.port
    mcp.settings.streamable_http_path = settings.server.path
    manager = BrowserSessionManager(settings)
    register_tools(mcp, manager, settings)
    return mcp


def run(settings: Settings | None = None) -> None:
    settings = settings or load_settings()
    if settings.runtime.install_browser_on_start:
        from cloakbrowser import ensure_binary

        ensure_binary()
    mcp = create_mcp_server(settings)
    mcp.run(transport=settings.server.transport)
