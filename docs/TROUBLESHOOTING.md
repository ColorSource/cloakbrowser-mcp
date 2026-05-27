# Troubleshooting

先运行：

```bash
cloakbrowser-mcp healthcheck --install-browser
cloakbrowser-mcp selftest
```

如果 MCP Host 已连接，先调用 `cloakbrowser_healthcheck`。所有失败项都会带
`suggested_fix`。

## MCP Host 连不上

检查：

- Host 配置中的 `command` 是否存在。
- `args` 是否能在终端直接运行。
- 源码方式是否设置了正确 `cwd`。
- stdio 模式不要额外打印非 MCP JSON 内容。

验证：

```bash
cloakbrowser-mcp tools-json
cloakbrowser-mcp print-config
```

## Binary Missing

症状：`browser_binary` 失败或 `BROWSER_LAUNCH_FAILED`。

修复：

```bash
cloakbrowser-mcp install
cloakbrowser-mcp healthcheck --probe-browser
```

如果下载源不可达：

```bash
export CLOAKBROWSER_BINARY_PATH=/path/to/chrome
```

## Linux 依赖缺失

症状：Chromium 启动失败，日志提到共享库、sandbox、GTK、X11。

修复：

```bash
playwright install-deps chromium
```

Dockerfile 已内置上游推荐依赖和字体。

## Headed 模式失败

症状：`Missing X server or $DISPLAY`。

修复：

```bash
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

Docker 镜像 entrypoint 会自动启动 Xvfb，并清理 stale lock。

## Proxy 页面卡住

先确认代理本身可用：

```bash
cloakbrowser-mcp healthcheck --check-proxy
```

处理顺序：

1. 临时关闭 `geoip`，确认不是 GeoIP 网络请求卡住。
2. provider 支持时改用 SOCKS5。
3. 对 Google/HTTP2/Client Hints 挂起，加入：

```bash
CLOAKBROWSER_MCP_EXTRA_ARGS=["--disable-features=AcceptCHFrame,CriticalClientHint"]
```

4. HTTP authenticated proxy 仍失败时，升级 cloakbrowser 到最新版。

## GeoIP 卡住或不准

确认：

```bash
CLOAKBROWSER_GEOIP_TIMEOUT_SECONDS=5
```

显式 timezone/locale 会覆盖 GeoIP：

```bash
CLOAKBROWSER_MCP_TIMEZONE=America/New_York
CLOAKBROWSER_MCP_LOCALE=en-US
```

## Cloudflare / DataDome / Turnstile

上游推荐组合：

- 住宅代理。
- `geoip=true`。
- `headless=false`。
- `humanize=true`。
- 持久 profile。

仅靠浏览器指纹不能解决 IP reputation 或账号/行为信誉问题。

## FingerprintJS Incognito / Baddriver

优先检查：

- 使用 persistent profile。
- 固定 fingerprint seed。
- screen width/height 与 viewport 一致。
- 需要时加 `--fingerprint-noise=false`。
- persistent context + FingerprintJS 场景可尝试 `--fingerprint-storage-quota=500`。

注意 storage quota 存在取舍：更高 quota 可能改善 incognito 检测，但影响 FingerprintJS。

## CDP 问题

`browser_start_cdp` 返回 `cdp.url` 和 `webSocketDebuggerUrl`。

排查：

- 端口是否被占用。
- 容器端口是否映射。
- Kubernetes/containerd 中 HTTP MCP 是否绑定 `0.0.0.0`。
- 不要把 CDP 裸端口暴露公网。

如果外部框架要求 per-seed CDP multiplexer，请参考上游 `cloakserve`。

## Windows Native 问题

上游 issues 中有 Windows native + SOCKS5、新页面挂起、reCAPTCHA 等开放问题。若相同代码在
Docker/Linux 正常，在 Windows native 异常，优先切换到 Docker/Linux 验证。

## 什么时候重读上游

- 升级 cloakbrowser 后。
- 反检测站点行为变化。
- proxy、GeoIP、CDP、Docker、Windows/macOS 平台问题。
- 本文 recipe 无效。
