"""浏览器会话状态。"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any


def _safe_url(page: Any) -> str | None:
    try:
        return page.url
    except Exception:
        return None


def _is_closed(page: Any) -> bool:
    try:
        return bool(page.is_closed())
    except Exception:
        return False


@dataclass
class BrowserSession:
    session_id: str
    mode: str
    context: Any
    browser: Any | None = None
    created_at: float = field(default_factory=time.time)
    profile_dir: str | None = None
    cdp_url: str | None = None
    pages: dict[str, Any] = field(default_factory=dict)
    active_page_id: str | None = None
    page_seq: int = field(default=0, repr=False)
    last_activity: float = field(default_factory=time.monotonic, repr=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False, compare=False)

    def touch(self) -> None:
        """更新最近活动时间，供空闲会话回收判断。"""
        self.last_activity = time.monotonic()

    def register_page(self, page: Any) -> str:
        # 幂等：context "page" 事件与显式 new_page 可能注册同一个 Page 对象。
        for pid, existing in self.pages.items():
            if existing is page:
                self.active_page_id = pid
                return pid
        self.page_seq += 1
        page_id = f"page-{self.page_seq}"
        self.pages[page_id] = page
        self.active_page_id = page_id
        return page_id

    def get_page(self, page_id: str | None = None) -> tuple[str, Any]:
        target_id = page_id or self.active_page_id
        if not target_id or target_id not in self.pages:
            raise KeyError("页面不存在。先调用 browser_new_page 或 browser_launch。")
        return target_id, self.pages[target_id]

    def drop_page(self, page_id: str) -> None:
        """从登记表移除某页，必要时把活动页指向最近的剩余页。"""
        self.pages.pop(page_id, None)
        if self.active_page_id == page_id:
            self.active_page_id = next(reversed(self.pages), None)

    def prune_closed(self) -> list[str]:
        """移除已被站点/用户关闭的页面，返回被清理的 page_id。"""
        removed = [pid for pid, page in list(self.pages.items()) if _is_closed(page)]
        for pid in removed:
            self.pages.pop(pid, None)
        if self.active_page_id not in self.pages:
            self.active_page_id = next(reversed(self.pages), None)
        return removed

    def summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "created_at": self.created_at,
            "profile_dir": self.profile_dir,
            "cdp_url": self.cdp_url,
            "active_page_id": self.active_page_id,
            "pages": [{"page_id": pid, "url": _safe_url(page)} for pid, page in self.pages.items()],
        }

    async def close(self) -> None:
        if self.context is not None:
            await self.context.close()
            self.context = None
        if self.browser is not None:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None
