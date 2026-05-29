from __future__ import annotations

import pytest

from cloakbrowser_mcp.browser import BrowserSessionManager
from cloakbrowser_mcp.config import Settings
from cloakbrowser_mcp.session import BrowserSession
from cloakbrowser_mcp.utils import ToolFailure


class _FakePage:
    def __init__(self, url: str = "https://x.example") -> None:
        self._url = url
        self._closed = False

    @property
    def url(self) -> str:
        return self._url

    def is_closed(self) -> bool:
        return self._closed

    async def close(self) -> None:
        self._closed = True


def _manager_with_session() -> tuple[BrowserSessionManager, BrowserSession]:
    manager = BrowserSessionManager(Settings())
    session = BrowserSession(session_id="s1", mode="context", context=object())
    manager.sessions["s1"] = session
    return manager, session


async def test_close_page_drops_and_reassigns_active():
    manager, session = _manager_with_session()
    p1 = session.register_page(_FakePage("https://a.example"))
    p2 = session.register_page(_FakePage("https://b.example"))

    result = await manager.close_page("s1", p2)

    assert result["closed_page"] == p2
    assert result["active_page_id"] == p1
    assert p2 not in session.pages


async def test_switch_page_sets_active():
    manager, session = _manager_with_session()
    p1 = session.register_page(_FakePage("https://a.example"))
    session.register_page(_FakePage("https://b.example"))

    result = await manager.switch_page("s1", p1)

    assert result["active_page_id"] == p1
    assert session.active_page_id == p1


async def test_switch_page_unknown_id_raises():
    manager, session = _manager_with_session()
    session.register_page(_FakePage())

    with pytest.raises(ToolFailure) as exc:
        await manager.switch_page("s1", "page-99")
    assert exc.value.error_code == "PAGE_NOT_FOUND"


def test_list_sessions_prunes_closed_pages():
    manager, session = _manager_with_session()
    open_page = _FakePage("https://open.example")
    closed_page = _FakePage("https://closed.example")
    closed_page._closed = True
    open_id = session.register_page(open_page)
    session.register_page(closed_page)

    pages = manager.list_sessions()["sessions"][0]["pages"]

    assert [p["page_id"] for p in pages] == [open_id]
    assert session.active_page_id == open_id
