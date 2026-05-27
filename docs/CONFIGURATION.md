# Configuration

配置优先级从低到高：

1. 代码默认值。
2. JSON/TOML 配置文件，路径来自 `--config` 或 `CLOAKBROWSER_MCP_CONFIG`。
3. `.env` 和环境变量。
4. MCP 工具调用中的 `options` 参数。

## Server

- `CLOAKBROWSER_MCP_TRANSPORT`：`stdio`、`sse`、`streamable-http`，默认 `stdio`。
- `CLOAKBROWSER_MCP_HOST`：HTTP/SSE 监听地址，默认 `127.0.0.1`。
- `CLOAKBROWSER_MCP_PORT`：HTTP/SSE 端口，默认 `8000`。
- `CLOAKBROWSER_MCP_PATH`：streamable HTTP path，默认 `/mcp`。
- `CLOAKBROWSER_MCP_STATELESS_HTTP`：HTTP 模式是否 stateless，默认 `true`。
- `CLOAKBROWSER_MCP_JSON_RESPONSE`：HTTP 响应是否 JSON，默认 `true`。

## Browser Launch

- `CLOAKBROWSER_MCP_LAUNCH_MODE`：`browser`、`context`、`persistent`，默认 `context`。
- `CLOAKBROWSER_MCP_HEADLESS`：默认 `true`。
- `CLOAKBROWSER_MCP_STEALTH_ARGS`：是否使用上游默认 stealth args，默认 `true`。
- `CLOAKBROWSER_MCP_BACKEND`：`playwright` 或 `patchright`，默认 `playwright`。
- `CLOAKBROWSER_MCP_TIMEOUT_MS`：页面动作默认超时，默认 `30000`。
- `CLOAKBROWSER_MCP_EXTRA_ARGS`：额外 Chromium flags，JSON 数组或逗号分隔。
- `CLOAKBROWSER_MCP_LAUNCH_KWARGS`：传给上游 launch 的 JSON 对象。

## Profile / Persistent Session

- `CLOAKBROWSER_MCP_PROFILE_ROOT`：profile 根目录，默认 `.cloakbrowser-mcp/profiles`。
- `CLOAKBROWSER_MCP_PROFILE_NAME`：默认 profile 名称，默认 `default`。
- `CLOAKBROWSER_MCP_USER_DATA_DIR`：显式 user data dir，优先级高于 profile name。
- `CLOAKBROWSER_MCP_PERSISTENT_SESSION`：默认强制使用 persistent 模式。

persistent 模式用于：

- 保持登录态。
- 避免空白 incognito profile。
- 加载 Chrome extension。
- 暖身 cookies/localStorage/cache。

## Proxy

- `CLOAKBROWSER_MCP_PROXY` 支持字符串或 JSON dict。
- 字符串：`http://user:pass@host:port`、`socks5://user:pass@host:port`。
- dict：`{"server":"http://host:port","username":"user","password":"pass","bypass":".google.com"}`。

proxy 建议：

- 高防目标优先住宅代理。
- provider 支持 SOCKS5 时优先 SOCKS5。
- HTTP proxy 卡住时尝试 `--disable-features=AcceptCHFrame,CriticalClientHint`。
- 开启 GeoIP 会通过 proxy 做出口 IP 解析。

## GeoIP / Timezone / Locale / Geolocation

- `CLOAKBROWSER_MCP_GEOIP`：默认 `false`。
- `CLOAKBROWSER_MCP_TIMEZONE`：IANA timezone，例如 `America/New_York`。
- `CLOAKBROWSER_MCP_LOCALE`：BCP 47 locale，例如 `en-US`。
- `CLOAKBROWSER_MCP_GEOLOCATION`：JSON 对象，例如
  `{"latitude":40.7128,"longitude":-74.0060}`。
- `CLOAKBROWSER_GEOIP_TIMEOUT_SECONDS`：上游 GeoIP 超时，默认建议 `5`。

显式 timezone/locale 优先于 GeoIP 自动推断。

## Fingerprint

- `CLOAKBROWSER_MCP_FINGERPRINT_SEED`：固定 seed，适合回访同一站点。
- `CLOAKBROWSER_MCP_FINGERPRINT_PLATFORM`：例如 `windows`、`macos`。
- `CLOAKBROWSER_MCP_FINGERPRINT_ARGS`：JSON 对象，映射到 `--fingerprint-*`。
- `CLOAKBROWSER_MCP_EXTRA_ARGS`：直接传 Chromium flags。

示例：

```bash
CLOAKBROWSER_MCP_FINGERPRINT_SEED=42069
CLOAKBROWSER_MCP_FINGERPRINT_ARGS={"noise":"false","screen-width":1920,"screen-height":1080}
```

## Humanize

- `CLOAKBROWSER_MCP_HUMANIZE`：默认 `false`。
- `CLOAKBROWSER_MCP_HUMAN_PRESET`：`default` 或 `careful`。
- `CLOAKBROWSER_MCP_HUMAN_CONFIG`：JSON 对象。

上游 humanize 会影响 Playwright Page/Locator 的 click、fill、type、scroll 等行为。
通过 CDP 由外部框架接管时，humanize 是 wrapper 层能力，不会自动跨进程生效。

## Extension

- `CLOAKBROWSER_MCP_EXTENSION_PATHS`：JSON 数组或逗号分隔路径。
- Chrome extension 通常需要 `persistent` + `headless=false`。

## Context

- `CLOAKBROWSER_MCP_USER_AGENT`
- `CLOAKBROWSER_MCP_VIEWPORT`：例如 `{"width":1920,"height":947}`。
- `CLOAKBROWSER_MCP_NO_VIEWPORT`
- `CLOAKBROWSER_MCP_COLOR_SCHEME`
- `CLOAKBROWSER_MCP_CONTEXT_KWARGS`：传给 Playwright context 的 JSON 对象。

## CDP

- `CLOAKBROWSER_MCP_CDP_HOST`：Chrome remote debugging bind host，默认 `127.0.0.1`。
- `CLOAKBROWSER_MCP_CDP_PORT`：固定端口；空值时自动分配。
- `CLOAKBROWSER_MCP_CDP_EXPOSE_HOST`：返回给调用方的 host，默认 `127.0.0.1`。
- `CLOAKBROWSER_MCP_CDP_TIMEOUT_SECONDS`：等待 CDP 就绪超时。

CDP 能完全控制浏览器。生产环境不要直接暴露到公网。

## Logging And Health

- `CLOAKBROWSER_MCP_LOG_LEVEL`
- `CLOAKBROWSER_MCP_LOG_FILE`
- `CLOAKBROWSER_MCP_INSTALL_BROWSER_ON_START`
- `CLOAKBROWSER_MCP_HEALTHCHECK_PROBE_BROWSER`
- `CLOAKBROWSER_MCP_CHECK_DOCKER`
- `CLOAKBROWSER_MCP_CHECK_NODE`

## Config File 示例

```toml
[server]
transport = "stdio"

[browser]
launch_mode = "persistent"
headless = false
proxy = "socks5://user:pass@host:1080"
geoip = true
humanize = true
profile_name = "agent-main"
extra_args = ["--fingerprint-storage-quota=500"]
```
