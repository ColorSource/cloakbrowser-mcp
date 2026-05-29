"""CloakBrowser 会话管理和页面动作。"""

from __future__ import annotations

import asyncio
import base64
import json
import socket
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel

from .config import Settings
from .session import BrowserSession
from .utils import ToolFailure, make_jsonable


class LaunchOptions(BaseModel):
    mode: Literal["browser", "context", "persistent"] | None = None
    headless: bool | None = None
    proxy: str | dict[str, Any] | None = None
    geoip: bool | None = None
    timezone: str | None = None
    locale: str | None = None
    geolocation: dict[str, float] | None = None
    fingerprint_seed: str | int | None = None
    fingerprint_platform: str | None = None
    fingerprint_args: dict[str, str | int | float | bool] | None = None
    extra_args: list[str] | None = None
    stealth_args: bool | None = None
    backend: Literal["playwright", "patchright"] | None = None
    humanize: bool | None = None
    human_preset: Literal["default", "careful"] | None = None
    human_config: dict[str, Any] | None = None
    profile_name: str | None = None
    user_data_dir: str | None = None
    persistent_session: bool | None = None
    extension_paths: list[str] | None = None
    user_agent: str | None = None
    viewport: dict[str, int] | None = None
    no_viewport: bool | None = None
    color_scheme: Literal["light", "dark", "no-preference"] | None = None
    context_kwargs: dict[str, Any] | None = None
    launch_kwargs: dict[str, Any] | None = None


class NavigateOptions(BaseModel):
    wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "load"
    timeout_ms: int | None = None
    referer: str | None = None


class ScreenshotOptions(BaseModel):
    path: str | None = None
    full_page: bool = True
    type: Literal["png", "jpeg"] = "png"
    quality: int | None = None
    omit_background: bool = False
    selector: str | None = None


class PdfOptions(BaseModel):
    path: str | None = None
    format: str = "A4"
    landscape: bool = False
    print_background: bool = True
    scale: float | None = None


class BrowserSessionManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.sessions: dict[str, BrowserSession] = {}
        self._reaper_task: asyncio.Task[None] | None = None

    async def launch_session(self, options: LaunchOptions | None = None) -> dict[str, Any]:
        opts = options or LaunchOptions()
        max_sessions = self.settings.runtime.max_sessions
        if max_sessions and len(self.sessions) >= max_sessions:
            raise ToolFailure(
                "SESSION_LIMIT_REACHED",
                f"已达到最大会话数 {max_sessions}。",
                "先用 browser_close 关闭不再使用的会话，或调高 CLOAKBROWSER_MCP_MAX_SESSIONS。",
                {"max_sessions": max_sessions, "open": len(self.sessions)},
            )
        mode = self._value(opts.mode, self.settings.browser.launch_mode)
        if self._value(opts.persistent_session, self.settings.browser.persistent_session):
            mode = "persistent"

        launch_args = self._build_args(opts)
        context_kwargs = self._build_context_kwargs(opts)
        launch_kwargs = self._value(opts.launch_kwargs, self.settings.browser.launch_kwargs) or {}
        profile_dir: str | None = None

        try:
            if mode == "browser":
                from cloakbrowser import launch_async

                browser = await launch_async(**launch_args, **launch_kwargs)
                context = await browser.new_context(**context_kwargs)
            elif mode == "persistent":
                from cloakbrowser import launch_persistent_context_async

                profile_dir = str(self._profile_dir(opts))
                Path(profile_dir).mkdir(parents=True, exist_ok=True)
                context = await launch_persistent_context_async(
                    profile_dir,
                    **launch_args,
                    **context_kwargs,
                    **launch_kwargs,
                )
                browser = None
            else:
                from cloakbrowser import launch_context_async

                context = await launch_context_async(
                    **launch_args,
                    **context_kwargs,
                    **launch_kwargs,
                )
                browser = None
        except Exception as exc:
            raise ToolFailure(
                "BROWSER_LAUNCH_FAILED",
                f"CloakBrowser 启动失败: {exc}",
                "先调用 cloakbrowser_healthcheck；若是 Linux 依赖缺失，运行 playwright install-deps chromium；若是代理/GeoIP 卡住，先关闭 geoip 或提高 CLOAKBROWSER_GEOIP_TIMEOUT_SECONDS。",
                {"mode": mode, "profile_dir": profile_dir},
            ) from exc

        session_id = f"session-{uuid.uuid4().hex[:12]}"
        session = BrowserSession(
            session_id=session_id,
            mode=mode,
            context=context,
            browser=browser,
            profile_dir=profile_dir,
        )
        # 自动捕获 window.open / target=_blank 等弹出的新标签页，并登记已存在的页面。
        context.on("page", session.register_page)
        for existing in context.pages:
            session.register_page(existing)
        page = await context.new_page()
        page_id = session.register_page(page)
        self.sessions[session_id] = session
        return {
            "session": session.summary(),
            "page_id": page_id,
            "launch_args": self._redacted_launch_summary(launch_args),
        }

    async def start_cdp_session(self, options: LaunchOptions | None = None) -> dict[str, Any]:
        opts = options or LaunchOptions()
        cdp_host = self.settings.cdp.host
        port = self.settings.cdp.port or _free_port()
        extra_args = list(opts.extra_args or self.settings.browser.extra_args)
        extra_args.extend(
            [
                f"--remote-debugging-port={port}",
                f"--remote-debugging-address={cdp_host}",
            ]
        )
        opts.extra_args = extra_args
        opts.mode = opts.mode or "browser"

        data = await self.launch_session(opts)
        session_id = data["session"]["session_id"]
        external_host = self.settings.cdp.expose_host
        cdp_url = f"http://{external_host}:{port}"
        await self._wait_for_cdp(cdp_host, port)
        version = await self._fetch_cdp_version(cdp_host, port)
        self.sessions[session_id].cdp_url = cdp_url
        return {
            **data,
            "cdp": {
                "url": cdp_url,
                "json_version": f"{cdp_url}/json/version",
                "webSocketDebuggerUrl": version.get("webSocketDebuggerUrl"),
            },
        }

    async def close_session(self, session_id: str | None = None) -> dict[str, Any]:
        if session_id is None:
            ids = list(self.sessions)
        else:
            ids = [session_id]
        closed: list[str] = []
        for sid in ids:
            session = self.sessions.pop(sid, None)
            if not session:
                continue
            async with session.lock:
                await session.close()
            closed.append(sid)
        return {"closed": closed, "remaining": list(self.sessions)}

    def list_sessions(self) -> dict[str, Any]:
        for session in self.sessions.values():
            session.prune_closed()
        return {"sessions": [session.summary() for session in self.sessions.values()]}

    async def shutdown(self) -> None:
        """服务关闭时调用：停止回收任务并统一关闭全部会话，避免残留 Chromium 进程。"""
        if self._reaper_task is not None:
            self._reaper_task.cancel()
            try:
                await self._reaper_task
            except asyncio.CancelledError:
                pass
            self._reaper_task = None
        await self.close_session()

    async def start_reaper(self) -> None:
        """按 session_idle_timeout_seconds 启动空闲会话回收后台任务（>0 才启用）。"""
        timeout = self.settings.runtime.session_idle_timeout_seconds
        if timeout and timeout > 0 and self._reaper_task is None:
            self._reaper_task = asyncio.create_task(self._reap_loop(timeout))

    async def _reap_loop(self, timeout: float) -> None:
        interval = max(5.0, min(timeout / 2, 60.0))
        while True:
            await asyncio.sleep(interval)
            await self._reap_idle(timeout)

    async def _reap_idle(self, timeout: float) -> None:
        now = time.monotonic()
        stale = [sid for sid, s in self.sessions.items() if now - s.last_activity > timeout]
        for sid in stale:
            await self.close_session(sid)

    async def new_page(self, session_id: str) -> dict[str, Any]:
        async with self._use_session(session_id) as session:
            page = await session.context.new_page()
            page_id = session.register_page(page)
            return {"session_id": session_id, "page_id": page_id, "pages": list(session.pages)}

    async def close_page(self, session_id: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_session(session_id) as session:
            try:
                target_id, page = session.get_page(page_id)
            except KeyError as exc:
                raise ToolFailure(
                    "PAGE_NOT_FOUND",
                    str(exc),
                    "传入有效 page_id，或用 browser_list_sessions 查看当前页面。",
                    {"session_id": session_id, "page_id": page_id},
                ) from exc
            try:
                await page.close()
            except Exception:
                pass
            session.drop_page(target_id)
            return {
                "closed_page": target_id,
                "active_page_id": session.active_page_id,
                "pages": list(session.pages),
            }

    async def switch_page(self, session_id: str, page_id: str) -> dict[str, Any]:
        async with self._use_session(session_id) as session:
            session.prune_closed()
            if page_id not in session.pages:
                raise ToolFailure(
                    "PAGE_NOT_FOUND",
                    f"找不到页面: {page_id}",
                    "用 browser_list_sessions 查看可用 page_id。",
                    {"session_id": session_id, "page_id": page_id},
                )
            session.active_page_id = page_id
            return {"active_page_id": page_id, "pages": list(session.pages)}

    @asynccontextmanager
    async def _use_session(self, session_id: str) -> AsyncIterator[BrowserSession]:
        """在会话锁内执行 context 级操作（new_page/cookies/storage 等），串行化同一会话。"""
        session = self._session(session_id)
        async with session.lock:
            session.touch()
            yield session

    @asynccontextmanager
    async def _use_page(self, session_id: str, page_id: str | None) -> AsyncIterator[Any]:
        """在会话锁内解析并操作页面。Playwright Page 非并发安全，需串行化。"""
        session = self._session(session_id)
        async with session.lock:
            session.touch()
            try:
                _, page = session.get_page(page_id)
            except KeyError as exc:
                raise ToolFailure(
                    "PAGE_NOT_FOUND",
                    str(exc),
                    "先调用 browser_new_page，或省略 page_id 使用当前活动页面。",
                    {"session_id": session_id, "page_id": page_id},
                ) from exc
            yield page

    async def _retry(self, func: Callable[[], Awaitable[Any]]) -> Any:
        """对易抖动的导航类操作做重试。重试次数取 runtime.retries（0 表示只尝试一次）。"""
        attempts = max(0, self.settings.runtime.retries) + 1
        last_exc: Exception | None = None
        for index in range(attempts):
            try:
                return await func()
            except Exception as exc:
                last_exc = exc
                if index + 1 >= attempts:
                    raise
                await asyncio.sleep(min(0.25 * (index + 1), 2.0))
        assert last_exc is not None  # pragma: no cover
        raise last_exc

    async def navigate(
        self,
        session_id: str,
        url: str,
        page_id: str | None = None,
        options: NavigateOptions | None = None,
    ) -> dict[str, Any]:
        opts = options or NavigateOptions()
        timeout = opts.timeout_ms or self.settings.runtime.timeout_ms
        async with self._use_page(session_id, page_id) as page:
            response = await self._retry(
                lambda: page.goto(url, wait_until=opts.wait_until, timeout=timeout, referer=opts.referer)
            )
            return {
                "url": page.url,
                "title": await page.title(),
                "status": response.status if response else None,
                "ok": response.ok if response else None,
            }

    async def click(self, session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.click(selector, timeout=self.settings.runtime.timeout_ms)
            return {"clicked": selector}

    async def fill(
        self,
        session_id: str,
        selector: str,
        value: str,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.fill(selector, value, timeout=self.settings.runtime.timeout_ms)
            return {"filled": selector}

    async def type_text(
        self,
        session_id: str,
        selector: str,
        text: str,
        page_id: str | None = None,
        delay_ms: int | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.type(selector, text, delay=delay_ms, timeout=self.settings.runtime.timeout_ms)
            return {"typed": selector, "characters": len(text)}

    async def press(
        self,
        session_id: str,
        selector: str,
        key: str,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.press(selector, key, timeout=self.settings.runtime.timeout_ms)
            return {"pressed": key, "selector": selector}

    async def hover(self, session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.hover(selector, timeout=self.settings.runtime.timeout_ms)
            return {"hovered": selector}

    async def select_option(
        self,
        session_id: str,
        selector: str,
        values: list[str] | None = None,
        labels: list[str] | None = None,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        if values is None and labels is None:
            raise ToolFailure(
                "INVALID_SELECT_OPTION",
                "select_option 需要 values 或 labels 之一。",
                "传入 values（option 的 value 列表）或 labels（可见文本列表）。",
                {"selector": selector},
            )
        async with self._use_page(session_id, page_id) as page:
            kwargs: dict[str, Any] = {"timeout": self.settings.runtime.timeout_ms}
            if values is not None:
                kwargs["value"] = values
            if labels is not None:
                kwargs["label"] = labels
            selected = await page.select_option(selector, **kwargs)
            return {"selector": selector, "selected": selected}

    async def set_input_files(
        self,
        session_id: str,
        selector: str,
        files: list[str],
        page_id: str | None = None,
    ) -> dict[str, Any]:
        paths = [str(Path(item).expanduser()) for item in files]
        async with self._use_page(session_id, page_id) as page:
            await page.set_input_files(selector, paths, timeout=self.settings.runtime.timeout_ms)
            return {"selector": selector, "files": paths}

    async def check(self, session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.check(selector, timeout=self.settings.runtime.timeout_ms)
            return {"checked": selector}

    async def uncheck(self, session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.uncheck(selector, timeout=self.settings.runtime.timeout_ms)
            return {"unchecked": selector}

    async def dblclick(self, session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.dblclick(selector, timeout=self.settings.runtime.timeout_ms)
            return {"double_clicked": selector}

    async def focus(self, session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.focus(selector, timeout=self.settings.runtime.timeout_ms)
            return {"focused": selector}

    async def scroll(
        self,
        session_id: str,
        selector: str | None = None,
        delta_x: int = 0,
        delta_y: int = 800,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            if selector:
                await page.locator(selector).scroll_into_view_if_needed(
                    timeout=self.settings.runtime.timeout_ms
                )
                return {"scrolled_into_view": selector}
            await page.mouse.wheel(delta_x, delta_y)
            return {"delta_x": delta_x, "delta_y": delta_y}

    async def reload(self, session_id: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            response = await self._retry(lambda: page.reload(timeout=self.settings.runtime.timeout_ms))
            return {
                "url": page.url,
                "title": await page.title(),
                "status": response.status if response else None,
                "ok": response.ok if response else None,
            }

    async def go_back(self, session_id: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            response = await self._retry(lambda: page.go_back(timeout=self.settings.runtime.timeout_ms))
            return {
                "url": page.url,
                "title": await page.title(),
                "status": response.status if response else None,
                "ok": response.ok if response else None,
            }

    async def go_forward(self, session_id: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            response = await self._retry(lambda: page.go_forward(timeout=self.settings.runtime.timeout_ms))
            return {
                "url": page.url,
                "title": await page.title(),
                "status": response.status if response else None,
                "ok": response.ok if response else None,
            }

    async def wait_for_selector(
        self,
        session_id: str,
        selector: str,
        page_id: str | None = None,
        state: Literal["attached", "detached", "visible", "hidden"] = "visible",
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            handle = await page.wait_for_selector(
                selector,
                state=state,
                timeout=timeout_ms or self.settings.runtime.timeout_ms,
            )
            return {"selector": selector, "state": state, "found": handle is not None}

    async def wait_for_load_state(
        self,
        session_id: str,
        state: str = "load",
        page_id: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        if state not in {"load", "domcontentloaded", "networkidle"}:
            raise ToolFailure(
                "INVALID_LOAD_STATE",
                f"不支持的 load state: {state}",
                "state 只能是 load、domcontentloaded 或 networkidle。",
                {"state": state},
            )
        async with self._use_page(session_id, page_id) as page:
            await page.wait_for_load_state(state, timeout=timeout_ms or self.settings.runtime.timeout_ms)
            return {"state": state, "url": page.url}

    async def wait_for_url(
        self,
        session_id: str,
        url: str,
        page_id: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.wait_for_url(url, timeout=timeout_ms or self.settings.runtime.timeout_ms)
            return {"url": page.url, "title": await page.title()}

    async def wait_for_timeout(
        self,
        session_id: str,
        timeout_ms: int,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            await page.wait_for_timeout(timeout_ms)
            return {"waited_ms": timeout_ms}

    async def evaluate(
        self,
        session_id: str,
        script: str,
        arg: Any | None = None,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            result = await page.evaluate(script, arg)
            return {"result": make_jsonable(result)}

    async def text(
        self,
        session_id: str,
        selector: str | None = None,
        page_id: str | None = None,
        max_chars: int | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            target = page.locator(selector) if selector else page.locator("body")
            content = await target.inner_text(timeout=self.settings.runtime.timeout_ms)
            return self._with_truncation(content, "text", max_chars)

    async def html(
        self,
        session_id: str,
        page_id: str | None = None,
        max_chars: int | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            content = await page.content()
            return self._with_truncation(content, "html", max_chars)

    def _with_truncation(self, content: str, key: str, max_chars: int | None) -> dict[str, Any]:
        limit = self.settings.runtime.max_output_chars if max_chars is None else max_chars
        total = len(content)
        if limit and total > limit:
            return {key: content[:limit], "truncated": True, "length": total, "returned": limit}
        return {key: content, "truncated": False, "length": total}

    async def get_attribute(
        self,
        session_id: str,
        selector: str,
        name: str,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            value = await page.get_attribute(selector, name, timeout=self.settings.runtime.timeout_ms)
            return {"selector": selector, "attribute": name, "value": value}

    async def is_visible(self, session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            return {"selector": selector, "visible": await page.is_visible(selector)}

    async def is_enabled(self, session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            return {"selector": selector, "enabled": await page.is_enabled(selector)}

    async def count(self, session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        async with self._use_page(session_id, page_id) as page:
            return {"selector": selector, "count": await page.locator(selector).count()}

    async def screenshot(
        self,
        session_id: str,
        page_id: str | None = None,
        options: ScreenshotOptions | None = None,
    ) -> dict[str, Any]:
        opts = options or ScreenshotOptions()
        kwargs: dict[str, Any] = {
            "type": opts.type,
            "omit_background": opts.omit_background,
            "timeout": self.settings.runtime.timeout_ms,
        }
        if opts.quality is not None:
            kwargs["quality"] = opts.quality
        if not opts.selector:
            # full_page 仅适用于整页截图；locator 截图不接受该参数。
            kwargs["full_page"] = opts.full_page
        async with self._use_page(session_id, page_id) as page:
            target = page.locator(opts.selector) if opts.selector else page
            if opts.path:
                path = Path(opts.path).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                await target.screenshot(path=str(path), **kwargs)
                return {"path": str(path)}
            raw = await target.screenshot(**kwargs)
            return {"image_bytes": raw, "type": opts.type}

    async def pdf(
        self,
        session_id: str,
        page_id: str | None = None,
        options: PdfOptions | None = None,
    ) -> dict[str, Any]:
        opts = options or PdfOptions()
        kwargs: dict[str, Any] = {
            "format": opts.format,
            "landscape": opts.landscape,
            "print_background": opts.print_background,
        }
        if opts.scale is not None:
            kwargs["scale"] = opts.scale
        async with self._use_page(session_id, page_id) as page:
            if opts.path:
                path = Path(opts.path).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                await page.pdf(path=str(path), **kwargs)
                return {"path": str(path)}
            raw = await page.pdf(**kwargs)
            return {"base64": base64.b64encode(raw).decode("ascii")}

    async def cookies(self, session_id: str, urls: list[str] | None = None) -> dict[str, Any]:
        async with self._use_session(session_id) as session:
            return {"cookies": await session.context.cookies(urls)}

    async def add_cookies(self, session_id: str, cookies: list[dict[str, Any]]) -> dict[str, Any]:
        async with self._use_session(session_id) as session:
            await session.context.add_cookies(cookies)
            return {"added": len(cookies)}

    async def clear_cookies(self, session_id: str) -> dict[str, Any]:
        async with self._use_session(session_id) as session:
            await session.context.clear_cookies()
            return {"cleared": True}

    async def storage_state(self, session_id: str, path: str | None = None) -> dict[str, Any]:
        async with self._use_session(session_id) as session:
            if path:
                target = Path(path).expanduser()
                target.parent.mkdir(parents=True, exist_ok=True)
                state = await session.context.storage_state(path=str(target))
                return {"path": str(target), "storage_state": state}
            return {"storage_state": await session.context.storage_state()}

    def profile_path(self, profile_name: str | None = None) -> dict[str, Any]:
        name = profile_name or self.settings.browser.profile_name
        root = self.settings.browser.profile_root
        return {"profile_name": name, "path": str((root / name).expanduser())}

    def list_profiles(self) -> dict[str, Any]:
        root = self.settings.browser.profile_root.expanduser()
        if not root.exists():
            return {"profile_root": str(root), "profiles": []}
        profiles = [
            {"name": path.name, "path": str(path)}
            for path in sorted(root.iterdir())
            if path.is_dir()
        ]
        return {"profile_root": str(root), "profiles": profiles}

    def _session(self, session_id: str) -> BrowserSession:
        session = self.sessions.get(session_id)
        if not session:
            raise ToolFailure(
                "SESSION_NOT_FOUND",
                f"找不到会话: {session_id}",
                "先调用 browser_launch 或 browser_list_sessions 获取有效 session_id。",
                {"session_id": session_id},
            )
        return session

    def _build_args(self, opts: LaunchOptions) -> dict[str, Any]:
        settings = self.settings.browser
        args = list(self._value(opts.extra_args, settings.extra_args) or [])

        seed = self._value(opts.fingerprint_seed, settings.fingerprint_seed)
        if seed is not None:
            args.append(f"--fingerprint={seed}")

        platform = self._value(opts.fingerprint_platform, settings.fingerprint_platform)
        if platform:
            args.append(f"--fingerprint-platform={platform}")

        geolocation = self._value(opts.geolocation, settings.geolocation)
        if geolocation and {"latitude", "longitude"}.issubset(geolocation):
            args.append(f"--fingerprint-location={geolocation['latitude']},{geolocation['longitude']}")

        fingerprint_args = self._value(opts.fingerprint_args, settings.fingerprint_args) or {}
        for key, value in fingerprint_args.items():
            normalized = key.replace("_", "-")
            args.append(f"--fingerprint-{normalized}={str(value).lower() if isinstance(value, bool) else value}")

        return {
            "headless": self._value(opts.headless, settings.headless),
            "proxy": self._value(opts.proxy, settings.proxy),
            "args": args,
            "stealth_args": self._value(opts.stealth_args, settings.stealth_args),
            "timezone": self._value(opts.timezone, settings.timezone),
            "locale": self._value(opts.locale, settings.locale),
            "geoip": self._value(opts.geoip, settings.geoip),
            "backend": self._value(opts.backend, settings.backend),
            "humanize": self._value(opts.humanize, settings.humanize),
            "human_preset": self._value(opts.human_preset, settings.human_preset),
            "human_config": self._value(opts.human_config, settings.human_config),
            "extension_paths": self._value(opts.extension_paths, settings.extension_paths),
        }

    def _build_context_kwargs(self, opts: LaunchOptions) -> dict[str, Any]:
        settings = self.settings.browser
        context_kwargs = dict(settings.context_kwargs)
        if opts.context_kwargs:
            context_kwargs.update(opts.context_kwargs)

        user_agent = self._value(opts.user_agent, settings.user_agent)
        if user_agent:
            context_kwargs["user_agent"] = user_agent

        if self._value(opts.no_viewport, settings.no_viewport):
            context_kwargs["viewport"] = None
        else:
            viewport = self._value(opts.viewport, settings.viewport)
            if viewport:
                context_kwargs["viewport"] = viewport

        color_scheme = self._value(opts.color_scheme, settings.color_scheme)
        if color_scheme:
            context_kwargs["color_scheme"] = color_scheme

        geolocation = self._value(opts.geolocation, settings.geolocation)
        if geolocation and {"latitude", "longitude"}.issubset(geolocation):
            context_kwargs["geolocation"] = {
                "latitude": float(geolocation["latitude"]),
                "longitude": float(geolocation["longitude"]),
            }
            permissions = set(context_kwargs.get("permissions") or [])
            permissions.add("geolocation")
            context_kwargs["permissions"] = sorted(permissions)

        return context_kwargs

    def _profile_dir(self, opts: LaunchOptions) -> Path:
        explicit = self._value(opts.user_data_dir, self.settings.browser.user_data_dir)
        if explicit:
            return Path(explicit).expanduser()
        name = self._value(opts.profile_name, self.settings.browser.profile_name)
        return self.settings.browser.profile_root.expanduser() / str(name)

    @staticmethod
    def _value(value: Any, default: Any) -> Any:
        return default if value is None else value

    @staticmethod
    def _redacted_launch_summary(launch_args: dict[str, Any]) -> dict[str, Any]:
        summary = dict(launch_args)
        proxy = summary.get("proxy")
        if isinstance(proxy, str) and "@" in proxy:
            scheme, rest = proxy.split("://", 1) if "://" in proxy else ("", proxy)
            host = rest.rsplit("@", 1)[-1]
            summary["proxy"] = f"{scheme}://***:***@{host}" if scheme else f"***:***@{host}"
        elif isinstance(proxy, dict) and proxy.get("password"):
            summary["proxy"] = {**proxy, "password": "***"}
        return make_jsonable(summary)

    async def _wait_for_cdp(self, host: str, port: int) -> None:
        deadline = time.monotonic() + self.settings.cdp.timeout_seconds
        url = f"http://{host}:{port}/json/version"
        async with httpx.AsyncClient(timeout=1.0) as client:
            while time.monotonic() < deadline:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(0.2)
        raise ToolFailure(
            "CDP_NOT_READY",
            f"CDP 端点未就绪: {url}",
            "检查 remote-debugging-address/port 是否被占用；在容器中确保端口已映射，并优先绑定 127.0.0.1 后由容器端口转发。",
        )

    @staticmethod
    async def _fetch_cdp_version(host: str, port: int) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{host}:{port}/json/version")
            response.raise_for_status()
            return response.json()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def dumps_compact(value: Any) -> str:
    return json.dumps(make_jsonable(value), ensure_ascii=False, separators=(",", ":"))
