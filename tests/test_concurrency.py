from __future__ import annotations

import asyncio

import pytest

from cloakbrowser_mcp.browser import BrowserSessionManager
from cloakbrowser_mcp.config import Settings
from cloakbrowser_mcp.session import BrowserSession
from cloakbrowser_mcp.utils import ToolFailure


class _FakePage:
    """记录并发度的假页面，用于验证串行化。"""

    def __init__(self, tracker: dict[str, int]) -> None:
        self.tracker = tracker

    async def work(self) -> None:
        self.tracker["active"] += 1
        self.tracker["max"] = max(self.tracker["max"], self.tracker["active"])
        await asyncio.sleep(0.02)
        self.tracker["active"] -= 1


def _session_with_page(tracker: dict[str, int]) -> BrowserSession:
    session = BrowserSession(session_id="s1", mode="context", context=object())
    session.register_page(_FakePage(tracker))
    return session


async def test_use_page_serializes_concurrent_operations():
    manager = BrowserSessionManager(Settings())
    tracker = {"active": 0, "max": 0}
    manager.sessions["s1"] = _session_with_page(tracker)

    async def op() -> None:
        async with manager._use_page("s1", None) as page:
            await page.work()

    await asyncio.gather(*(op() for _ in range(5)))

    assert tracker["max"] == 1  # operations never overlapped


async def test_use_page_raises_when_no_page():
    manager = BrowserSessionManager(Settings())
    manager.sessions["s1"] = BrowserSession(session_id="s1", mode="context", context=object())

    with pytest.raises(ToolFailure) as exc:
        async with manager._use_page("s1", None):
            pass
    assert exc.value.error_code == "PAGE_NOT_FOUND"
