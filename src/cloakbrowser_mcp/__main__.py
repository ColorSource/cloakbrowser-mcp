"""命令行入口。"""

from __future__ import annotations

import argparse
import json
import sys

from .config import Settings, load_settings, settings_for_display
from .healthcheck import run_healthcheck_sync
from .logging import configure_logging
from .server import run
from .tools import TOOL_DEFINITIONS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cloakbrowser-mcp")
    parser.add_argument("--config", help="JSON/TOML 配置文件路径。")
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="启动 MCP 服务。")
    serve.add_argument("--transport", choices=["stdio", "sse", "streamable-http"])
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.add_argument("--path")

    health = sub.add_parser("healthcheck", help="运行自检。")
    health.add_argument("--install-browser", action="store_true")
    health.add_argument("--probe-browser", action="store_true")
    health.add_argument("--check-proxy", action="store_true")
    health.add_argument("--check-docker", action="store_true")
    health.add_argument("--check-cdp", action="store_true")
    health.add_argument("--json", action="store_true", default=True)

    sub.add_parser("selftest", help="运行安装后自检：安装 binary、探测浏览器、检查 CDP。")
    sub.add_parser("install", help="预下载 CloakBrowser Chromium。")
    sub.add_parser("tools-json", help="输出本 MCP 工具目录。")
    sub.add_parser("print-config", help="输出当前合并后的配置。")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "serve"

    settings = load_settings(args.config)
    settings = _apply_cli_overrides(settings, args)
    configure_logging(settings.runtime.log_level, settings.runtime.log_file)

    if command == "serve":
        run(settings)
        return 0
    if command == "healthcheck":
        data = run_healthcheck_sync(
            settings,
            install_browser=args.install_browser,
            probe_browser=args.probe_browser,
            check_proxy=args.check_proxy,
            check_docker=args.check_docker,
            check_cdp=args.check_cdp,
        )
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0 if data.get("ok") else 1
    if command == "selftest":
        data = run_healthcheck_sync(
            settings,
            install_browser=True,
            probe_browser=True,
            check_proxy=bool(settings.browser.proxy),
            check_docker=settings.runtime.check_docker,
            check_cdp=True,
        )
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0 if data.get("ok") else 1
    if command == "install":
        from cloakbrowser import binary_info, ensure_binary

        path = ensure_binary()
        print(json.dumps({"ok": True, "path": path, "binary_info": binary_info()}, ensure_ascii=False, indent=2))
        return 0
    if command == "tools-json":
        print(json.dumps({"tools": TOOL_DEFINITIONS}, ensure_ascii=False, indent=2))
        return 0
    if command == "print-config":
        print(json.dumps(settings_for_display(settings), ensure_ascii=False, indent=2))
        return 0
    parser.error(f"未知命令: {command}")
    return 2


def _apply_cli_overrides(settings: Settings, args: argparse.Namespace) -> Settings:
    if getattr(args, "transport", None):
        settings.server.transport = args.transport
    if getattr(args, "host", None):
        settings.server.host = args.host
    if getattr(args, "port", None):
        settings.server.port = args.port
    if getattr(args, "path", None):
        settings.server.path = args.path
    return settings


if __name__ == "__main__":
    sys.exit(main())
