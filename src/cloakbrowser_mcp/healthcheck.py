"""安装和运行环境自检。"""

from __future__ import annotations

import asyncio
import importlib.util
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Any

import httpx

from .config import Settings
from .utils import make_jsonable


def check(
    name: str,
    ok: bool,
    message: str,
    suggested_fix: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "ok": ok,
        "message": message,
        "suggested_fix": suggested_fix,
        "details": details or {},
    }


async def run_healthcheck(
    settings: Settings,
    install_browser: bool = False,
    probe_browser: bool | None = None,
    check_proxy: bool = False,
    check_docker: bool | None = None,
    check_cdp: bool = False,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    checks.append(_python_check())
    checks.append(_package_manager_check())
    if settings.runtime.check_node:
        checks.append(_node_check())
    checks.extend(_cloakbrowser_checks(install_browser=install_browser))
    checks.append(_playwright_check())
    checks.append(await _mcp_schema_check(settings))
    checks.append(_profile_check(settings))
    checks.append(_headed_check(settings))

    if check_proxy and settings.browser.proxy:
        checks.append(await _proxy_check(settings))

    if check_docker if check_docker is not None else settings.runtime.check_docker:
        checks.append(_docker_check())

    should_probe = settings.runtime.healthcheck_probe_browser if probe_browser is None else probe_browser
    if should_probe:
        checks.append(await _browser_probe(settings, check_cdp=check_cdp))

    ok = all(item["ok"] for item in checks)
    return make_jsonable(
        {
            "ok": ok,
            "summary": {
                "passed": sum(1 for item in checks if item["ok"]),
                "failed": sum(1 for item in checks if not item["ok"]),
            },
            "checks": checks,
        }
    )


def _python_check() -> dict[str, Any]:
    version = sys.version_info
    ok = version >= (3, 10)
    return check(
        "python",
        ok,
        f"Python {platform.python_version()}",
        None if ok else "安装 Python 3.10 或更高版本。",
        {"executable": sys.executable},
    )


def _package_manager_check() -> dict[str, Any]:
    managers = {name: shutil.which(name) for name in ("uv", "pip", "pipx")}
    ok = any(managers.values())
    return check(
        "package_manager",
        ok,
        "找到 Python 包管理器。" if ok else "未找到 uv/pip/pipx。",
        None if ok else "安装 uv，或确保 pip 在 PATH 中。",
        managers,
    )


def _node_check() -> dict[str, Any]:
    node = shutil.which("node")
    npm = shutil.which("npm")
    available = bool(node and npm)
    return check(
        "node",
        True,
        "找到 Node.js/npm。" if available else "未找到 Node.js/npm；纯 Python MCP stdio 不强制需要。",
        None if available else "仅当需要 MCP Inspector、npx 或 Playwright MCP 对比测试时安装 Node.js 20+。",
        {"node": node, "npm": npm, "available": available},
    )


def _cloakbrowser_checks(install_browser: bool) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    spec = importlib.util.find_spec("cloakbrowser")
    if spec is None:
        return [
            check(
                "cloakbrowser_package",
                False,
                "未安装 cloakbrowser 包。",
                "运行 uv pip install -e . 或 pip install cloakbrowser-mcp。",
            )
        ]

    try:
        import cloakbrowser
        from cloakbrowser import binary_info, ensure_binary

        info = binary_info()
        checks.append(
            check(
                "cloakbrowser_package",
                True,
                f"cloakbrowser {getattr(cloakbrowser, '__version__', 'unknown')} 可导入。",
                details=info,
            )
        )
        installed = bool(info.get("installed"))
        if install_browser and not installed:
            path = ensure_binary()
            info = binary_info()
            checks.append(
                check("browser_binary", True, "已下载 CloakBrowser Chromium。", details={"path": path, **info})
            )
        else:
            checks.append(
                check(
                    "browser_binary",
                    installed,
                    "CloakBrowser Chromium 已安装。" if installed else "CloakBrowser Chromium 尚未下载。",
                    None
                    if installed
                    else "运行 cloakbrowser-mcp install，或 python -m cloakbrowser install；也可设置 CLOAKBROWSER_BINARY_PATH。",
                    info,
                )
            )
    except Exception as exc:
        checks.append(
            check(
                "cloakbrowser_package",
                False,
                f"cloakbrowser 检查失败: {exc}",
                "升级 cloakbrowser 或运行 cloakbrowser-mcp healthcheck --install-browser。",
                {"type": exc.__class__.__name__},
            )
        )
    return checks


def _playwright_check() -> dict[str, Any]:
    spec = importlib.util.find_spec("playwright")
    ok = spec is not None
    return check(
        "playwright",
        ok,
        "Playwright 可导入。" if ok else "Playwright 不可导入。",
        None if ok else "重新安装依赖：uv pip install -e .",
    )


async def _mcp_schema_check(settings: Settings) -> dict[str, Any]:
    try:
        from .server import create_mcp_server

        server = create_mcp_server(settings)
        tools = await server.list_tools()
        names = [tool.name for tool in tools]
        unique = len(names) == len(set(names))
        ok = bool(names) and unique
        return check(
            "mcp_tool_schema",
            ok,
            f"已声明 {len(names)} 个 MCP 工具。" if ok else "MCP 工具 schema 声明异常。",
            None if ok else "运行 cloakbrowser-mcp tools-json；检查重复工具名或 tools.py 注册失败。",
            {"tool_count": len(names), "unique": unique},
        )
    except Exception as exc:
        return check(
            "mcp_tool_schema",
            False,
            f"MCP 工具 schema 检查失败: {exc}",
            "运行 cloakbrowser-mcp tools-json 查看具体错误。",
            {"type": exc.__class__.__name__},
        )


def _profile_check(settings: Settings) -> dict[str, Any]:
    root = settings.browser.profile_root.expanduser()
    try:
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=root, delete=True) as handle:
            handle.write(b"ok")
        return check("profile_dir", True, "profile 根目录可读写。", details={"path": str(root)})
    except Exception as exc:
        return check(
            "profile_dir",
            False,
            f"profile 根目录不可读写: {exc}",
            "修改 CLOAKBROWSER_MCP_PROFILE_ROOT 到当前用户可写目录。",
            {"path": str(root), "type": exc.__class__.__name__},
        )


def _headed_check(settings: Settings) -> dict[str, Any]:
    if settings.browser.headless:
        return check("headed_display", True, "默认 headless=true，不需要显示服务。")
    if platform.system() in {"Windows", "Darwin"}:
        return check("headed_display", True, "当前系统通常可直接运行 headed 模式。")
    display = os.environ.get("DISPLAY")
    ok = bool(display)
    return check(
        "headed_display",
        ok,
        f"DISPLAY={display}" if ok else "headless=false 但未设置 DISPLAY。",
        None if ok else "在 Linux/Docker 中启动 Xvfb，例如 Xvfb :99 -screen 0 1920x1080x24 并设置 DISPLAY=:99。",
    )


async def _proxy_check(settings: Settings) -> dict[str, Any]:
    proxy = settings.browser.proxy
    if isinstance(proxy, dict):
        proxy_url = proxy.get("server")
    else:
        proxy_url = proxy
    if not proxy_url:
        return check("proxy", True, "未配置代理，跳过代理连通性检查。")
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
            response = await client.get("https://api.ipify.org?format=json")
            response.raise_for_status()
            return check("proxy", True, "代理可连通。", details=response.json())
    except Exception as exc:
        return check(
            "proxy",
            False,
            f"代理连通性失败: {exc}",
            "确认代理 URL、认证和出口网络；HTTP 代理访问 Google 卡住时优先尝试 SOCKS5 或 --disable-features=AcceptCHFrame,CriticalClientHint。",
            {"proxy": _redact_proxy(proxy_url), "type": exc.__class__.__name__},
        )


def _docker_check() -> dict[str, Any]:
    docker = shutil.which("docker")
    if not docker:
        return check("docker", False, "未找到 docker。", "如需容器模式，安装 Docker Desktop 或 Docker Engine。")
    try:
        result = subprocess.run(
            [docker, "info", "--format", "{{json .ServerVersion}}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return check("docker", True, "Docker daemon 可用。", details={"version": result.stdout.strip()})
    except Exception as exc:
        return check(
            "docker",
            False,
            f"Docker daemon 不可用: {exc}",
            "启动 Docker daemon；Windows/macOS 上确认 Docker Desktop 已运行。",
            {"type": exc.__class__.__name__},
        )


async def _browser_probe(settings: Settings, check_cdp: bool) -> dict[str, Any]:
    from .browser import BrowserSessionManager, LaunchOptions

    manager = BrowserSessionManager(settings)
    try:
        options = LaunchOptions(mode="browser" if check_cdp else "context", headless=settings.browser.headless)
        data = await manager.start_cdp_session(options) if check_cdp else await manager.launch_session(options)
        session_id = data["session"]["session_id"]
        await manager.navigate(session_id, "data:text/html,<title>ok</title><main>ok</main>")
        await manager.close_session(session_id)
        message = "最小浏览器启动、CDP 和页面加载成功。" if check_cdp else "最小浏览器启动和页面加载成功。"
        return check("browser_probe", True, message)
    except Exception as exc:
        await manager.close_session()
        return check(
            "browser_probe",
            False,
            f"最小浏览器启动失败: {exc}",
            "先运行 cloakbrowser-mcp install；Linux 缺系统库时运行 playwright install-deps chromium；headed 模式缺 DISPLAY 时启用 Xvfb。",
            {"type": exc.__class__.__name__},
        )


def _redact_proxy(proxy: str) -> str:
    if "@" not in proxy:
        return proxy
    scheme, rest = proxy.split("://", 1) if "://" in proxy else ("", proxy)
    host = rest.rsplit("@", 1)[-1]
    return f"{scheme}://***:***@{host}" if scheme else f"***:***@{host}"


def run_healthcheck_sync(settings: Settings, **kwargs: Any) -> dict[str, Any]:
    return asyncio.run(run_healthcheck(settings, **kwargs))
