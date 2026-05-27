from __future__ import annotations

import os

import pytest

from cloakbrowser_mcp.browser import BrowserSessionManager, LaunchOptions
from cloakbrowser_mcp.config import Settings


@pytest.mark.browser
@pytest.mark.asyncio
async def test_basic_browser_flow():
    if os.environ.get("CLOAKBROWSER_MCP_RUN_BROWSER_TESTS") != "1":
        pytest.skip("Set CLOAKBROWSER_MCP_RUN_BROWSER_TESTS=1 to launch CloakBrowser.")

    settings = Settings()
    settings.browser.headless = True
    manager = BrowserSessionManager(settings)
    data = await manager.launch_session(LaunchOptions(mode="context", headless=True))
    session_id = data["session"]["session_id"]
    nav = await manager.navigate(session_id, "data:text/html,<title>Hello</title><main>Hello MCP</main>")
    text = await manager.text(session_id)
    await manager.close_session(session_id)

    assert nav["title"] == "Hello"
    assert "Hello MCP" in text["text"]
