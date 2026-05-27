# Upstream Notes

事实来源：[CloakHQ/CloakBrowser](https://github.com/CloakHQ/CloakBrowser)

## 当前参考版本

- 上游仓库：`https://github.com/CloakHQ/CloakBrowser`
- 分析 commit：`14ec2ebf5f952b3dcc8ee019965cc48cbf7ccf53`
- README 标注最新版本：`v0.3.31`
- 最新 Chromium：`146.0.7680.177.5`
- 上游 Python 包名：`cloakbrowser`

## 上游主要能力

- patched Chromium binary，指纹补丁在 C++ 源码层实现。
- Python API：`launch()`、`launch_async()`、`launch_context()`、
  `launch_context_async()`、`launch_persistent_context()`、
  `launch_persistent_context_async()`。
- Playwright 兼容对象：Browser、BrowserContext、Page。
- proxy：HTTP、SOCKS5、Playwright proxy dict。
- GeoIP：从 proxy 出口 IP 自动推断 timezone/locale，并注入 WebRTC IP spoof。
- fingerprint：seed、platform、GPU、screen、timezone、locale、location、storage quota、
  fonts、WebRTC IP、noise 等 flags。
- humanize：鼠标、键盘、滚动和 Locator/Page 行为补丁。
- persistent profile：cookies、localStorage、cache、扩展和历史状态持久化。
- Chrome extension：`extension_paths`。
- Docker：官方镜像含 Chromium 依赖、字体、Xvfb、`cloaktest`、`cloakserve`。
- CDP：上游 `cloakserve` 支持 CDP multiplexer 和 per-seed 参数。
- JS/Node wrapper：Playwright 与 Puppeteer。

## 上游安装方式

Python：

```bash
pip install cloakbrowser
pip install cloakbrowser[geoip]
python -m cloakbrowser install
python -m cloakbrowser info
```

JavaScript：

```bash
npm install cloakbrowser playwright-core
npm install cloakbrowser puppeteer-core
```

Docker：

```bash
docker run --rm cloakhq/cloakbrowser cloaktest
docker run -d -p 127.0.0.1:9222:9222 cloakhq/cloakbrowser cloakserve
```

## 上游推荐配置

高防站点常用组合：

- 住宅代理，不要仅依赖数据中心 IP。
- `geoip=True`，让 timezone/locale 与 proxy 出口匹配。
- `headless=False`，部分站点仍能区分 headless。
- `humanize=True`，使用上游行为层。
- 持久 profile 用于登录态、cookie 暖身和非 incognito 行为。

FingerprintJS 相关：

- `--fingerprint-noise=false`
- screen width/height 与 viewport 匹配。
- persistent context 可按目标选择 storage quota。
- 上游 issue #320 中建议 persistent + FingerprintJS 场景加入
  `--fingerprint-storage-quota=500`。

Proxy 相关：

- HTTP authenticated proxy 曾受 Playwright CDP auth handler 影响；新版上游已改进。
- Google/HTTP2/Client Hints 挂起可试
  `--disable-features=AcceptCHFrame,CriticalClientHint`。
- 如果 provider 支持 SOCKS5，优先尝试 SOCKS5。

## examples 对 MCP 设计的启发

- `basic.py` 映射为 `browser_launch`、`browser_navigate`、`browser_get_text`。
- `persistent_context.py` 映射为 `mode=persistent`、`profile_name/user_data_dir`、
  `browser_storage_state`。
- `stealth_test.py` 和 `fingerprint_scan_test.py` 映射为 healthcheck 与文档 recipe。
- `examples/integrations/` 说明外部框架可通过 binary path 或 CDP 接入；本 MCP 提供
  `browser_start_cdp`。
- Docker 示例说明容器需系统库、字体、Xvfb、CDP 健康检查；本仓库 Dockerfile 直接内置。

## issues 中常见问题归纳

- #206：用户希望 MCP Server；维护者提到可用 Playwright MCP 指向 CloakBrowser binary，
  也认可 dedicated MCP 可提供 stealth args、GeoIP、humanize 和简化配置。
- #274：agent-friendly CLI 需求，包括 doctor、profile、open、screenshot、dump、eval。
  本 MCP 对应实现 healthcheck、profile、screenshot、evaluate 和结构化返回。
- #283：Docker restart 后 Xvfb stale lock 造成 Chrome 502；本镜像 entrypoint 会清理
  `/tmp/.X99-lock` 和 `/tmp/.X11-unix/X99`。
- #286：containerd/Kubernetes 没有 Docker marker，`cloakserve` 可能绑定 loopback；本 MCP
  HTTP transport 支持显式 `--host 0.0.0.0`。
- #207：GeoIP 在高负载下曾卡住；上游 v0.3.28 后用
  `CLOAKBROWSER_GEOIP_TIMEOUT_SECONDS` 限时。
- #243/#182：代理访问 Google 卡住，涉及 authenticated HTTP proxy、Playwright CDP auth、
  AcceptCHFrame/CriticalClientHint；文档给出 SOCKS5 和 disable-features recipe。
- #314：CDP + Cloudflare 失败排查方向仍是 headed、住宅代理、GeoIP、humanize。
- #320：FingerprintJS 对 persistent context 报 incognito/baddriver 时检查 storage quota。
- #304/#316：Windows native + SOCKS5 或新页面挂起仍有开放问题；必要时切换 Docker/Linux。
- #281：上游明确不支持自动化创建新账号；AI Agent 遇到此类任务应询问人工。

## 已映射到 MCP 的能力

- 安装与 binary info：`cloakbrowser_install`、`cloakbrowser_binary_info`。
- 健康检查：`cloakbrowser_healthcheck`。
- `launch_async()` / `launch_context_async()` / `launch_persistent_context_async()`：
  `browser_launch`。
- proxy、GeoIP、timezone、locale、geolocation、fingerprint flags、humanize、extension：
  `LaunchOptions` 和环境变量。
- 页面动作：navigate、click、fill、type、press、wait、evaluate、text、html、screenshot。
- Cookie 和 storage_state。
- profile path/list。
- CDP：`browser_start_cdp` 启动单会话 CDP endpoint。

## 暂未映射或仅部分映射

- 上游 JS/Puppeteer wrapper 未直接暴露为 MCP 工具。
- 上游 `cloakserve` 的 per-seed CDP multiplexer 没有完整重写；本 MCP 提供单会话 CDP。
- noVNC/Profile Manager UI 不在本 MCP 范围内。
- CAPTCHA solver、proxy rotation、账号注册自动化不内置。
- 删除 profile 未做默认工具，避免误删真实浏览器状态。

## 上游更新后的同步流程

1. 拉取上游最新 README、examples、Dockerfile、CHANGELOG 和 issues。
2. 更新 `pyproject.toml` 中的 `cloakbrowser` 版本约束。
3. 运行 `cloakbrowser-mcp healthcheck --install-browser --probe-browser`。
4. 对照上游新增参数更新 `LaunchOptions`、`.env.example`、`docs/CONFIGURATION.md`。
5. 对照上游新增能力更新 `docs/TOOLS.md`。
6. 更新本文件的 commit、版本、能力映射和常见问题。
7. 跑单元测试；必要时启用浏览器 smoke test。
