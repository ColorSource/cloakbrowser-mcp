from __future__ import annotations

import pytest

from cloakbrowser_mcp.browser import BrowserSessionManager
from cloakbrowser_mcp.config import Settings


def _manager(retries: int) -> BrowserSessionManager:
    settings = Settings()
    settings.runtime.retries = retries
    return BrowserSessionManager(settings)


async def test_retry_succeeds_after_transient_failures():
    manager = _manager(retries=2)
    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    assert await manager._retry(flaky) == "ok"
    assert calls["n"] == 3


async def test_retry_raises_after_exhausting_attempts():
    manager = _manager(retries=1)
    calls = {"n": 0}

    async def always_fail():
        calls["n"] += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await manager._retry(always_fail)
    assert calls["n"] == 2  # 1 initial attempt + 1 retry


async def test_retry_disabled_runs_once():
    manager = _manager(retries=0)
    calls = {"n": 0}

    async def always_fail():
        calls["n"] += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await manager._retry(always_fail)
    assert calls["n"] == 1
