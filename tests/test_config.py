from __future__ import annotations

import json

from cloakbrowser_mcp.config import load_settings


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("CLOAKBROWSER_MCP_HEADLESS", "false")
    monkeypatch.setenv("CLOAKBROWSER_MCP_GEOIP", "true")
    monkeypatch.setenv("CLOAKBROWSER_MCP_EXTRA_ARGS", '["--disable-http2"]')
    settings = load_settings()
    assert settings.browser.headless is False
    assert settings.browser.geoip is True
    assert settings.browser.extra_args == ["--disable-http2"]


def test_config_file_merge(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "server": {"transport": "stdio"},
                "browser": {"launch_mode": "persistent", "profile_name": "agent"},
            }
        ),
        encoding="utf-8",
    )
    settings = load_settings(path)
    assert settings.server.transport == "stdio"
    assert settings.browser.launch_mode == "persistent"
    assert settings.browser.profile_name == "agent"


def test_proxy_dict_env(monkeypatch):
    monkeypatch.setenv(
        "CLOAKBROWSER_MCP_PROXY",
        '{"server":"http://proxy:8080","username":"u","password":"p"}',
    )
    settings = load_settings()
    assert settings.browser.proxy["server"] == "http://proxy:8080"
