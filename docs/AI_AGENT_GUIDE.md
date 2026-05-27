# AI Agent Guide

本文件是给 AI Agent 的操作手册。你拿到本仓库后，应优先按这里的顺序安装、配置、
启动、验证和使用 CloakBrowser MCP。

## 1. Read This First

本项目是 MCP Server，不是 CloakBrowser 上游本体。底层 stealth Chromium、浏览器
二进制下载、fingerprint patches、proxy/GeoIP/humanize/CDP 行为都来自
[CloakBrowser upstream](https://github.com/CloakHQ/CloakBrowser)。

默认策略：

- 所有已实现 MCP 工具默认可用。
- 不需要额外权限开关。
- 失败时先读工具返回的 `error.error_code`、`message`、`suggested_fix`。
- 每次新环境先运行 `cloakbrowser_healthcheck` 或命令行 `cloakbrowser-mcp healthcheck`。

## 2. How This MCP Relates To CloakBrowser

CloakBrowser 提供 patched Chromium 和 Playwright/Puppeteer 兼容包装。本 MCP 做三件事：

- 把上游能力映射成稳定 MCP 工具。
- 给 AI Agent 提供统一配置、健康检查和排障流程。
- 管理浏览器 session/page/profile/CDP 生命周期。

不要把 MCP 层当成新的反检测实现。遇到 fingerprint、proxy、CDP、headless、GeoIP
问题时，应以上游 README、examples、CHANGELOG 和相关 issues 为事实来源。

## 3. Upstream Reading Order

需要理解或排障时按此顺序阅读：

1. 先读 CloakBrowser README：确认当前推荐安装、launch 参数、fingerprint、humanize、
   Docker、CDP 和 troubleshooting。
2. 再读 examples：重点看 `basic.py`、`persistent_context.py`、`stealth_test.py`、
   `fingerprint_scan_test.py` 和 `examples/integrations/`。
3. 再读 Docker 相关文件：上游 `Dockerfile`、`bin/docker-entrypoint.sh`、
   `bin/cloakserve`。
4. 再读 issues 中与当前失败相关的内容：proxy、GeoIP、CDP、Cloudflare、FingerprintJS、
   Xvfb、Windows SOCKS5 等。
5. 再回到本 MCP 的 [`docs/CONFIGURATION.md`](CONFIGURATION.md) 和
   [`docs/TOOLS.md`](TOOLS.md)，把上游建议映射到 MCP 配置或工具参数。

## 4. Installation Decision Tree

优先选择：

- 只需要本地 MCP Host：使用 `uvx cloakbrowser-mcp`。
- 已 clone 本仓库并要开发：使用 `uv sync` 和 `uv run cloakbrowser-mcp`。
- Host 需要 HTTP MCP 或隔离运行：使用 Docker Compose。
- 需要外部框架通过 CDP 连接：使用 `browser_start_cdp`，或直接参考上游 `cloakserve`。

如果没有 `uv`：

```bash
python -m pip install cloakbrowser-mcp
cloakbrowser-mcp healthcheck --install-browser
cloakbrowser-mcp
```

## 5. Minimal Setup

```bash
uvx cloakbrowser-mcp healthcheck --install-browser
uvx cloakbrowser-mcp
```

如果包未发布到 PyPI，用仓库链接直接运行：

```bash
uvx --from git+<this-repo-url> cloakbrowser-mcp healthcheck --install-browser
uvx --from git+<this-repo-url> cloakbrowser-mcp
```

在源码目录：

```bash
uv sync
uv run cloakbrowser-mcp healthcheck --install-browser
uv run cloakbrowser-mcp
```

如果浏览器 binary 下载失败：

- 重试 `cloakbrowser-mcp install`。
- 或设置 `CLOAKBROWSER_BINARY_PATH=/path/to/chrome`。
- 或设置上游变量 `CLOAKBROWSER_DOWNLOAD_URL`。

## 6. MCP Host Configuration

stdio 配置：

```json
{
  "mcpServers": {
    "cloakbrowser": {
      "command": "uvx",
      "args": ["cloakbrowser-mcp"],
      "env": {
        "CLOAKBROWSER_MCP_HEADLESS": "true"
      }
    }
  }
}
```

源码目录配置：

```json
{
  "mcpServers": {
    "cloakbrowser": {
      "command": "uv",
      "args": ["run", "cloakbrowser-mcp"],
      "cwd": "/absolute/path/to/cloakbrowser-mcp"
    }
  }
}
```

HTTP transport：

```bash
cloakbrowser-mcp serve --transport streamable-http --host 127.0.0.1 --port 8000 --path /mcp
```

Host URL 使用 `http://127.0.0.1:8000/mcp`。

## 7. First Successful Browser Run

连接 MCP 后按顺序调用：

1. `cloakbrowser_healthcheck`，参数可先用默认值。
2. `browser_launch`，最小参数为 `{}`。
3. `browser_navigate`，传入 `session_id` 和 URL。
4. `browser_get_text` 或 `browser_screenshot` 验证页面状态。
5. `browser_close` 关闭会话。

示例工具调用思路：

```json
{
  "options": {
    "mode": "context",
    "headless": true
  }
}
```

如果需要保持登录态：

```json
{
  "options": {
    "mode": "persistent",
    "profile_name": "work-account",
    "headless": false
  }
}
```

## 8. Tool Discovery And Usage Strategy

MCP Host 会通过 `tools/list` 自动读取工具 schema。命令行可用：

```bash
cloakbrowser-mcp tools-json
```

调用策略：

- 环境检查：`cloakbrowser_healthcheck`。
- 二进制安装：`cloakbrowser_install`。
- 普通自动化：`browser_launch` → `browser_navigate` → 页面动作工具。
- 页面历史控制：`browser_reload`、`browser_go_back`、`browser_go_forward`。
- 登录态和反 incognito：`mode=persistent` 或 `CLOAKBROWSER_MCP_PERSISTENT_SESSION=true`。
- 外部框架需要接管：`browser_start_cdp`。
- Cookie/session 迁移：`browser_get_cookies`、`browser_add_cookies`、`browser_storage_state`。
- profile 路径：`profile_resolve`、`profile_list`。

## 9. Configuration Recipes

普通本地 headless：

```bash
CLOAKBROWSER_MCP_HEADLESS=true
CLOAKBROWSER_MCP_LAUNCH_MODE=context
```

高防站点优先配置：

```bash
CLOAKBROWSER_MCP_PROXY=http://user:pass@residential-proxy:port
CLOAKBROWSER_MCP_GEOIP=true
CLOAKBROWSER_MCP_HEADLESS=false
CLOAKBROWSER_MCP_HUMANIZE=true
```

固定设备身份：

```bash
CLOAKBROWSER_MCP_FINGERPRINT_SEED=42069
CLOAKBROWSER_MCP_PERSISTENT_SESSION=true
```

FingerprintJS 针对性排查：

```bash
CLOAKBROWSER_MCP_EXTRA_ARGS=["--fingerprint-noise=false","--fingerprint-screen-width=1920","--fingerprint-screen-height=1080","--fingerprint-storage-quota=500"]
```

proxy 出现 Google/HTTP2/Client Hints 挂起：

```bash
CLOAKBROWSER_MCP_EXTRA_ARGS=["--disable-features=AcceptCHFrame,CriticalClientHint"]
```

加载扩展：

```bash
CLOAKBROWSER_MCP_LAUNCH_MODE=persistent
CLOAKBROWSER_MCP_HEADLESS=false
CLOAKBROWSER_MCP_EXTENSION_PATHS=["/absolute/path/to/extension"]
```

## 10. Troubleshooting Decision Tree

1. MCP Host 连不上：确认 command/args/cwd；命令行运行同一命令。
2. tools/list 失败：运行 `cloakbrowser-mcp tools-json` 和 `cloakbrowser-mcp healthcheck`。
3. browser launch 失败：运行 `cloakbrowser-mcp healthcheck --install-browser --probe-browser`。
4. Linux/Docker headed 失败：确认 Xvfb 和 `DISPLAY=:99`。
5. proxy 页面卡住：先不用 GeoIP 测试 proxy，再试 SOCKS5 或 AcceptCHFrame workaround。
6. GeoIP 卡住：设置 `CLOAKBROWSER_GEOIP_TIMEOUT_SECONDS=5` 或临时关闭 GeoIP。
7. Cloudflare/DataDome/Turnstile 失败：用 headed、住宅代理、GeoIP、humanize。
8. FingerprintJS incognito/baddriver：检查 persistent profile、storage quota、screen/viewport。
9. CDP 连接不稳：确认端口可访问；优先本地 loopback；外部公开前加网络隔离。
10. Windows SOCKS5/页面空白：查看上游相关 Windows issue，必要时改用 Docker/Linux。

## 11. How To Recover From Common Failures

- `BROWSER_LAUNCH_FAILED`：先 `cloakbrowser_install`，再 healthcheck probe。
- 安装后完整自检：命令行运行 `cloakbrowser-mcp selftest`。
- `SESSION_NOT_FOUND`：重新调用 `browser_launch`，不要复用旧 session_id。
- `PAGE_NOT_FOUND`：省略 page_id 使用活动页，或调用 `browser_new_page`。
- binary missing：`cloakbrowser-mcp install`。
- Linux deps missing：`playwright install-deps chromium`。
- macOS Gatekeeper：参考上游 README 的 `xattr -cr ~/.cloakbrowser/...`。
- Docker restart 后 headed 失败：检查 `/tmp/.X99-lock`，本镜像 entrypoint 会自动清理。
- Kubernetes/containerd 端口不可达：显式设置 HTTP transport `--host 0.0.0.0`，并用 Service/port-forward 连接。

## 12. When To Re-Check Upstream Documentation

出现以下情况必须重新查上游：

- CloakBrowser 版本升级。
- 检测站点、Captcha、Cloudflare、Akamai、Kasada 行为变化。
- proxy、GeoIP、timezone、locale、fingerprint flags 调整。
- Docker、CDP、Xvfb、Kubernetes 部署异常。
- Windows/macOS 平台特有问题。
- MCP 工具返回 suggested_fix 仍无法解决。

## 13. When To Ask The Human

需要人工输入时再问：

- 需要代理、账号、登录验证码、目标站点授权信息。
- 目标任务可能违反站点规则或缺少合法访问权限。
- 需要选择是否使用住宅代理、是否切换 Docker/Linux、是否启用 headed。
- 需要删除或迁移真实 profile 数据。
- 上游 issue 显示当前平台存在未修复 bug，需要业务侧选择等待、降级或换环境。
