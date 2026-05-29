"""FastMCP 服务入口。"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

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


def _build_lifespan(
    manager: BrowserSessionManager,
) -> Callable[[FastMCP], AbstractAsyncContextManager[None]]:
    """返回一个 lifespan，在服务关闭时统一关闭所有浏览器会话，避免进程残留。"""

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[None]:
        await manager.start_reaper()
        try:
            yield
        finally:
            await manager.shutdown()

    return lifespan


def create_mcp_server(settings: Settings | None = None) -> FastMCP:
    settings = settings or load_settings()
    manager = BrowserSessionManager(settings)
    mcp = FastMCP(
        settings.server.name,
        instructions=SERVER_INSTRUCTIONS,
        stateless_http=settings.server.stateless_http,
        json_response=settings.server.json_response,
        streamable_http_path=settings.server.path,
        lifespan=_build_lifespan(manager),
    )
    mcp.settings.host = settings.server.host
    mcp.settings.port = settings.server.port
    mcp.settings.streamable_http_path = settings.server.path
    register_tools(mcp, manager, settings)
    return mcp


def run(settings: Settings | None = None) -> None:
    settings = settings or load_settings()
    if settings.runtime.install_browser_on_start:
        from cloakbrowser import ensure_binary

        ensure_binary()
    mcp = create_mcp_server(settings)
    mcp.run(transport=settings.server.transport)
