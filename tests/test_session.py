from __future__ import annotations

from cloakbrowser_mcp.session import BrowserSession


class _FakePage:
    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def url(self) -> str:
        return self._url


def _session() -> BrowserSession:
    return BrowserSession(session_id="s", mode="context", context=object())


def test_register_page_is_idempotent_for_same_object():
    session = _session()
    page = _FakePage("https://a.example")
    first = session.register_page(page)
    second = session.register_page(page)
    assert first == second
    assert len(session.pages) == 1


def test_register_page_ids_are_monotonic_after_removal():
    session = _session()
    first = session.register_page(_FakePage("https://a.example"))
    session.register_page(_FakePage("https://b.example"))
    assert first == "page-1"
    del session.pages[first]
    third = session.register_page(_FakePage("https://c.example"))
    assert third == "page-3"  # ids never reused


def test_summary_reports_page_urls():
    session = _session()
    session.register_page(_FakePage("https://example.com"))
    summary = session.summary()
    assert summary["active_page_id"] == "page-1"
    assert summary["pages"] == [{"page_id": "page-1", "url": "https://example.com"}]
