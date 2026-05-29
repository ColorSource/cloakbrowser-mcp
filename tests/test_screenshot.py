from __future__ import annotations

from cloakbrowser_mcp.browser import BrowserSessionManager
from cloakbrowser_mcp.config import Settings
from cloakbrowser_mcp.session import BrowserSession


class _ShotPage:
    def __init__(self) -> None:
        self.kwargs: dict | None = None

    @property
    def url(self) -> str:
        return "https://x.example"

    def is_closed(self) -> bool:
        return False

    async def screenshot(self, **kwargs: object) -> bytes:
        self.kwargs = dict(kwargs)
        return b"\x89PNG-fake-bytes"


async def test_screenshot_returns_raw_bytes_inline():
    manager = BrowserSessionManager(Settings())
    session = BrowserSession(session_id="s1", mode="context", context=object())
    page = _ShotPage()
    session.register_page(page)
    manager.sessions["s1"] = session

    result = await manager.screenshot("s1")

    assert result["image_bytes"] == b"\x89PNG-fake-bytes"
    assert result["type"] == "png"
    # full_page is only sent for whole-page screenshots (no selector).
    assert page.kwargs is not None and page.kwargs.get("full_page") is True
