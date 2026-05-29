from __future__ import annotations

from cloakbrowser_mcp.browser import BrowserSessionManager, LaunchOptions
from cloakbrowser_mcp.config import Settings


def test_storage_state_path_is_expanded_into_context_kwargs():
    settings = Settings()
    settings.browser.storage_state = "~/state.json"
    kwargs = BrowserSessionManager(settings)._build_context_kwargs(LaunchOptions())
    assert "storage_state" in kwargs
    assert kwargs["storage_state"].endswith("state.json")
    assert "~" not in kwargs["storage_state"]


def test_storage_state_dict_is_passed_through():
    state = {"cookies": [], "origins": []}
    kwargs = BrowserSessionManager(Settings())._build_context_kwargs(LaunchOptions(storage_state=state))
    assert kwargs["storage_state"] == state


def test_no_storage_state_by_default():
    kwargs = BrowserSessionManager(Settings())._build_context_kwargs(LaunchOptions())
    assert "storage_state" not in kwargs
