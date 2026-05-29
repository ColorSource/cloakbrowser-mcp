from __future__ import annotations

from cloakbrowser_mcp.browser import BrowserSessionManager
from cloakbrowser_mcp.config import Settings


def _manager(limit: int) -> BrowserSessionManager:
    settings = Settings()
    settings.runtime.max_output_chars = limit
    return BrowserSessionManager(settings)


def test_truncation_cuts_and_marks():
    result = _manager(10)._with_truncation("x" * 25, "text", None)
    assert result["truncated"] is True
    assert result["length"] == 25
    assert result["returned"] == 10
    assert result["text"] == "x" * 10


def test_no_truncation_under_limit():
    result = _manager(100)._with_truncation("hello", "html", None)
    assert result["truncated"] is False
    assert result["length"] == 5
    assert result["html"] == "hello"


def test_per_call_override_can_disable_truncation():
    result = _manager(5)._with_truncation("hello world", "text", 0)
    assert result["truncated"] is False
    assert result["text"] == "hello world"
