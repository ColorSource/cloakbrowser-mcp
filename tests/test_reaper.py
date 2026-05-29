from __future__ import annotations

import time

import pytest

from cloakbrowser_mcp.browser import BrowserSessionManager
from cloakbrowser_mcp.config import Settings
from cloakbrowser_mcp.session import BrowserSession
from cloakbrowser_mcp.utils import ToolFailure


class _FakeContext:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


async def test_launch_rejects_when_at_max_sessions():
    settings = Settings()
    settings.runtime.max_sessions = 1
    manager = BrowserSessionManager(settings)
    manager.sessions["s1"] = BrowserSession(session_id="s1", mode="context", context=_FakeContext())

    with pytest.raises(ToolFailure) as exc:
        await manager.launch_session()
    assert exc.value.error_code == "SESSION_LIMIT_REACHED"


async def test_reap_idle_closes_only_stale_sessions():
    settings = Settings()
    settings.runtime.session_idle_timeout_seconds = 10.0
    manager = BrowserSessionManager(settings)

    stale_ctx = _FakeContext()
    stale = BrowserSession(session_id="stale", mode="context", context=stale_ctx)
    stale.last_activity = time.monotonic() - 100
    fresh_ctx = _FakeContext()
    fresh = BrowserSession(session_id="fresh", mode="context", context=fresh_ctx)
    fresh.last_activity = time.monotonic()
    manager.sessions["stale"] = stale
    manager.sessions["fresh"] = fresh

    await manager._reap_idle(settings.runtime.session_idle_timeout_seconds)

    assert "stale" not in manager.sessions
    assert stale_ctx.closed is True
    assert "fresh" in manager.sessions
    assert fresh_ctx.closed is False


async def test_reaper_disabled_by_default():
    manager = BrowserSessionManager(Settings())
    await manager.start_reaper()
    assert manager._reaper_task is None
    await manager.shutdown()  # must be a no-op without a reaper
