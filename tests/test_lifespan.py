from __future__ import annotations

from cloakbrowser_mcp.browser import BrowserSessionManager
from cloakbrowser_mcp.config import Settings
from cloakbrowser_mcp.server import _build_lifespan
from cloakbrowser_mcp.session import BrowserSession


class _FakeContext:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


async def test_lifespan_closes_sessions_on_shutdown():
    manager = BrowserSessionManager(Settings())
    ctx = _FakeContext()
    manager.sessions["s1"] = BrowserSession(session_id="s1", mode="context", context=ctx)

    lifespan = _build_lifespan(manager)
    async with lifespan(None):  # type: ignore[arg-type]
        assert "s1" in manager.sessions

    assert manager.sessions == {}
    assert ctx.closed is True
