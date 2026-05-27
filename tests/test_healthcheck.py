from __future__ import annotations

import pytest

from cloakbrowser_mcp.config import Settings
from cloakbrowser_mcp.healthcheck import run_healthcheck


@pytest.mark.asyncio
async def test_healthcheck_without_browser_probe(tmp_path):
    settings = Settings()
    settings.browser.profile_root = tmp_path / "profiles"
    data = await run_healthcheck(settings, install_browser=False, probe_browser=False)
    names = {item["name"] for item in data["checks"]}
    assert "python" in names
    assert "profile_dir" in names
    assert "cloakbrowser_package" in names
