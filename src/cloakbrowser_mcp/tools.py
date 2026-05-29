"""MCP 工具注册。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .browser import BrowserSessionManager, LaunchOptions, NavigateOptions, ScreenshotOptions
from .config import Settings, settings_for_display
from .healthcheck import run_healthcheck
from .utils import fail_from_exception, ok

TOOL_DEFINITIONS: list[dict[str, str]] = [
    {"name": "cloakbrowser_get_status", "description": "返回 MCP 服务配置摘要、已注册工具和当前会话。"},
    {"name": "cloakbrowser_healthcheck", "description": "检查 Python、CloakBrowser、浏览器二进制、profile、Docker、proxy、CDP 等运行条件。"},
    {"name": "cloakbrowser_install", "description": "预下载或确认 CloakBrowser Chromium 二进制。"},
    {"name": "cloakbrowser_binary_info", "description": "返回上游 cloakbrowser.binary_info() 的结构化结果。"},
    {"name": "profile_resolve", "description": "解析持久 profile 名称到本地路径。"},
    {"name": "profile_list", "description": "列出 MCP profile 根目录下已有 profile。"},
    {"name": "browser_launch", "description": "启动 browser/context/persistent 会话并创建第一页。"},
    {"name": "browser_start_cdp", "description": "启动带 Chrome DevTools Protocol 端口的 CloakBrowser 会话。"},
    {"name": "browser_list_sessions", "description": "列出当前 MCP 进程管理的浏览器会话。"},
    {"name": "browser_close", "description": "关闭指定会话；不传 session_id 时关闭全部会话。"},
    {"name": "browser_new_page", "description": "在已有会话中创建新页面。"},
    {"name": "browser_navigate", "description": "打开 URL 并返回标题、最终 URL 和响应状态。"},
    {"name": "browser_click", "description": "点击 CSS/文本等 Playwright selector。"},
    {"name": "browser_fill", "description": "填充输入框。humanize=true 时由上游行为层处理节奏。"},
    {"name": "browser_type", "description": "按字符输入文本，可设置 delay_ms。"},
    {"name": "browser_press", "description": "向 selector 发送键盘按键。"},
    {"name": "browser_hover", "description": "悬停到 selector。"},
    {"name": "browser_select_option", "description": "选择 <select> 下拉项，可按 value 或可见文本 label。"},
    {"name": "browser_set_input_files", "description": "给 file input 设置一个或多个本地文件路径。"},
    {"name": "browser_check", "description": "勾选 checkbox 或 radio。"},
    {"name": "browser_uncheck", "description": "取消勾选 checkbox。"},
    {"name": "browser_reload", "description": "刷新当前页面。"},
    {"name": "browser_go_back", "description": "后退到浏览器历史上一页。"},
    {"name": "browser_go_forward", "description": "前进到浏览器历史下一页。"},
    {"name": "browser_wait_for_selector", "description": "等待元素达到 visible/hidden/attached/detached 状态。"},
    {"name": "browser_evaluate", "description": "在页面中执行 JavaScript 并返回 JSON 可序列化结果。"},
    {"name": "browser_get_text", "description": "读取 body 或指定 selector 的可见文本。"},
    {"name": "browser_get_html", "description": "读取当前页面 HTML。"},
    {"name": "browser_get_attribute", "description": "读取元素属性值（href/src/value 等）。"},
    {"name": "browser_is_visible", "description": "判断元素当前是否可见。"},
    {"name": "browser_is_enabled", "description": "判断元素当前是否可交互。"},
    {"name": "browser_count", "description": "返回匹配 selector 的元素数量。"},
    {"name": "browser_screenshot", "description": "截图并返回 base64，或写入 path。"},
    {"name": "browser_get_cookies", "description": "读取当前 context cookies。"},
    {"name": "browser_add_cookies", "description": "向当前 context 添加 cookies。"},
    {"name": "browser_clear_cookies", "description": "清空当前 context cookies。"},
    {"name": "browser_storage_state", "description": "读取或保存 Playwright storage_state。"},
]


def register_tools(mcp: FastMCP, manager: BrowserSessionManager, settings: Settings) -> None:
    @mcp.tool()
    def cloakbrowser_get_status() -> dict[str, Any]:
        """返回 MCP 服务配置、工具目录和当前会话。"""
        try:
            return ok(
                {
                    "settings": settings_for_display(settings),
                    "tools": TOOL_DEFINITIONS,
                    **manager.list_sessions(),
                }
            )
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def cloakbrowser_healthcheck(
        install_browser: bool = False,
        probe_browser: bool = False,
        check_proxy: bool = False,
        check_docker: bool = False,
        check_cdp: bool = False,
    ) -> dict[str, Any]:
        """运行结构化自检。失败项会包含 suggested_fix，供 AI Agent 自动修复。"""
        try:
            data = await run_healthcheck(
                settings,
                install_browser=install_browser,
                probe_browser=probe_browser,
                check_proxy=check_proxy,
                check_docker=check_docker,
                check_cdp=check_cdp,
            )
            return data
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    def cloakbrowser_install() -> dict[str, Any]:
        """下载或确认 CloakBrowser Chromium 二进制。"""
        try:
            from cloakbrowser import binary_info, ensure_binary

            path = ensure_binary()
            return ok({"path": path, "binary_info": binary_info()})
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    def cloakbrowser_binary_info() -> dict[str, Any]:
        """返回上游 binary_info()。"""
        try:
            from cloakbrowser import binary_info

            return ok({"binary_info": binary_info()})
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    def profile_resolve(profile_name: str | None = None) -> dict[str, Any]:
        """解析 profile 名称到持久目录路径。"""
        try:
            return ok(manager.profile_path(profile_name))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    def profile_list() -> dict[str, Any]:
        """列出已存在的 profile 目录。"""
        try:
            return ok(manager.list_profiles())
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_launch(options: LaunchOptions | None = None) -> dict[str, Any]:
        """启动 CloakBrowser 会话。options 可覆盖默认 browser 配置。"""
        try:
            return ok(await manager.launch_session(options))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_start_cdp(options: LaunchOptions | None = None) -> dict[str, Any]:
        """启动带 remote-debugging-port 的会话，并返回 CDP URL。"""
        try:
            return ok(await manager.start_cdp_session(options))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    def browser_list_sessions() -> dict[str, Any]:
        """列出当前会话。"""
        try:
            return ok(manager.list_sessions())
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_close(session_id: str | None = None) -> dict[str, Any]:
        """关闭一个或全部会话。"""
        try:
            return ok(await manager.close_session(session_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_new_page(session_id: str) -> dict[str, Any]:
        """在指定会话中新建页面。"""
        try:
            return ok(await manager.new_page(session_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_navigate(
        session_id: str,
        url: str,
        page_id: str | None = None,
        options: NavigateOptions | None = None,
    ) -> dict[str, Any]:
        """导航到 URL。"""
        try:
            return ok(await manager.navigate(session_id, url, page_id, options))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_click(session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        """点击 selector。"""
        try:
            return ok(await manager.click(session_id, selector, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_fill(
        session_id: str,
        selector: str,
        value: str,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        """填充输入值。"""
        try:
            return ok(await manager.fill(session_id, selector, value, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_type(
        session_id: str,
        selector: str,
        text: str,
        page_id: str | None = None,
        delay_ms: int | None = None,
    ) -> dict[str, Any]:
        """按字符输入文本。"""
        try:
            return ok(await manager.type_text(session_id, selector, text, page_id, delay_ms))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_press(
        session_id: str,
        selector: str,
        key: str,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        """发送键盘按键。"""
        try:
            return ok(await manager.press(session_id, selector, key, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_hover(session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        """悬停到 selector。"""
        try:
            return ok(await manager.hover(session_id, selector, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_select_option(
        session_id: str,
        selector: str,
        values: list[str] | None = None,
        labels: list[str] | None = None,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        """选择下拉项。传 values（option value）或 labels（可见文本）之一。"""
        try:
            return ok(await manager.select_option(session_id, selector, values, labels, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_set_input_files(
        session_id: str,
        selector: str,
        files: list[str],
        page_id: str | None = None,
    ) -> dict[str, Any]:
        """给 file input 设置本地文件。"""
        try:
            return ok(await manager.set_input_files(session_id, selector, files, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_check(session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        """勾选 checkbox/radio。"""
        try:
            return ok(await manager.check(session_id, selector, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_uncheck(session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        """取消勾选 checkbox。"""
        try:
            return ok(await manager.uncheck(session_id, selector, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_reload(session_id: str, page_id: str | None = None) -> dict[str, Any]:
        """刷新当前页面。"""
        try:
            return ok(await manager.reload(session_id, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_go_back(session_id: str, page_id: str | None = None) -> dict[str, Any]:
        """后退到浏览器历史上一页。"""
        try:
            return ok(await manager.go_back(session_id, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_go_forward(session_id: str, page_id: str | None = None) -> dict[str, Any]:
        """前进到浏览器历史下一页。"""
        try:
            return ok(await manager.go_forward(session_id, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_wait_for_selector(
        session_id: str,
        selector: str,
        page_id: str | None = None,
        state: str = "visible",
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        """等待 selector 状态。"""
        try:
            if state not in {"attached", "detached", "visible", "hidden"}:
                return {
                    "ok": False,
                    "error": {
                        "error_code": "INVALID_SELECTOR_STATE",
                        "message": f"不支持的 selector state: {state}",
                        "suggested_fix": "state 只能是 attached、detached、visible 或 hidden。",
                        "details": {"state": state},
                    },
                }
            return ok(
                await manager.wait_for_selector(
                    session_id,
                    selector,
                    page_id,
                    state,  # type: ignore[arg-type]
                    timeout_ms,
                )
            )
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_evaluate(
        session_id: str,
        script: str,
        arg: Any | None = None,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        """执行 JavaScript。"""
        try:
            return ok(await manager.evaluate(session_id, script, arg, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_get_text(
        session_id: str,
        selector: str | None = None,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        """读取页面文本。"""
        try:
            return ok(await manager.text(session_id, selector, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_get_html(session_id: str, page_id: str | None = None) -> dict[str, Any]:
        """读取页面 HTML。"""
        try:
            return ok(await manager.html(session_id, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_get_attribute(
        session_id: str,
        selector: str,
        name: str,
        page_id: str | None = None,
    ) -> dict[str, Any]:
        """读取元素属性值。"""
        try:
            return ok(await manager.get_attribute(session_id, selector, name, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_is_visible(session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        """判断元素是否可见。"""
        try:
            return ok(await manager.is_visible(session_id, selector, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_is_enabled(session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        """判断元素是否可交互。"""
        try:
            return ok(await manager.is_enabled(session_id, selector, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_count(session_id: str, selector: str, page_id: str | None = None) -> dict[str, Any]:
        """返回匹配 selector 的元素数量。"""
        try:
            return ok(await manager.count(session_id, selector, page_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_screenshot(
        session_id: str,
        page_id: str | None = None,
        options: ScreenshotOptions | None = None,
    ) -> dict[str, Any]:
        """截图。"""
        try:
            return ok(await manager.screenshot(session_id, page_id, options))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_get_cookies(session_id: str, urls: list[str] | None = None) -> dict[str, Any]:
        """读取 cookies。"""
        try:
            return ok(await manager.cookies(session_id, urls))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_add_cookies(session_id: str, cookies: list[dict[str, Any]]) -> dict[str, Any]:
        """添加 cookies。"""
        try:
            return ok(await manager.add_cookies(session_id, cookies))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_clear_cookies(session_id: str) -> dict[str, Any]:
        """清空 cookies。"""
        try:
            return ok(await manager.clear_cookies(session_id))
        except Exception as exc:
            return fail_from_exception(exc)

    @mcp.tool()
    async def browser_storage_state(session_id: str, path: str | None = None) -> dict[str, Any]:
        """读取或保存 storage_state。"""
        try:
            return ok(await manager.storage_state(session_id, path))
        except Exception as exc:
            return fail_from_exception(exc)
