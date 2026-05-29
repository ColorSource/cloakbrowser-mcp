# Tools

所有工具默认启用。所有工具返回 JSON；成功时包含 `ok: true`，失败时包含：

```json
{
  "ok": false,
  "error": {
    "error_code": "BROWSER_LAUNCH_FAILED",
    "message": "...",
    "suggested_fix": "...",
    "details": {}
  }
}
```

## 推荐调用顺序

1. `cloakbrowser_healthcheck`
2. `browser_launch` 或 `browser_start_cdp`
3. 页面动作工具
4. Cookie/storage/profile 工具按需调用
5. `browser_close`

## Runtime Tools

### `cloakbrowser_get_status`

返回合并后的配置摘要、工具目录和当前 session 列表。proxy 密码会被脱敏。

### `cloakbrowser_healthcheck`

参数：

- `install_browser`：是否下载上游 Chromium。
- `probe_browser`：是否做最小浏览器启动。
- `check_proxy`：是否测试代理连通性。
- `check_docker`：是否测试 Docker daemon。
- `check_cdp`：是否在浏览器 probe 中附带 CDP 检查。

用途：环境初检和失败自修复入口。

### `cloakbrowser_install`

调用上游 `ensure_binary()` 下载或确认 Chromium binary。

### `cloakbrowser_binary_info`

返回上游 `binary_info()`。

## Profile Tools

### `profile_resolve`

参数：

- `profile_name`：可选。

返回 profile 名称对应的持久目录路径。

### `profile_list`

列出 `CLOAKBROWSER_MCP_PROFILE_ROOT` 下已有 profile。

## Launch Tools

### `browser_launch`

参数：

- `options`：可选对象，覆盖默认配置。

`options` 主要字段：

- `mode`：`browser`、`context`、`persistent`。
- `headless`
- `proxy`
- `geoip`
- `timezone`
- `locale`
- `geolocation`
- `fingerprint_seed`
- `fingerprint_platform`
- `fingerprint_args`
- `extra_args`
- `stealth_args`
- `backend`
- `humanize`
- `human_preset`
- `human_config`
- `profile_name`
- `user_data_dir`
- `persistent_session`
- `extension_paths`
- `user_agent`
- `viewport`
- `no_viewport`
- `color_scheme`
- `context_kwargs`
- `launch_kwargs`

返回：

- `session.session_id`
- `page_id`
- `session.profile_dir`
- 脱敏后的 launch 摘要

### `browser_start_cdp`

与 `browser_launch` 类似，但附加 remote debugging port 并返回：

- `cdp.url`
- `cdp.json_version`
- `cdp.webSocketDebuggerUrl`

用于 browser-use、Crawl4AI、Scrapling、Playwright 外部脚本等 CDP 接入。

## Session Tools

### `browser_list_sessions`

列出当前 MCP 进程管理的 session。

### `browser_close`

参数：

- `session_id`：可选。不传时关闭全部 session。

## Page Tools

### `browser_new_page`

参数：

- `session_id`

返回新 `page_id`。

### `browser_navigate`

参数：

- `session_id`
- `url`
- `page_id`：可选。
- `options.wait_until`：`commit`、`domcontentloaded`、`load`、`networkidle`。
- `options.timeout_ms`
- `options.referer`

返回最终 URL、标题、响应状态。

### `browser_click`

参数：

- `session_id`
- `selector`
- `page_id`：可选。

### `browser_fill`

参数：

- `session_id`
- `selector`
- `value`
- `page_id`：可选。

### `browser_type`

参数：

- `session_id`
- `selector`
- `text`
- `page_id`：可选。
- `delay_ms`：可选。

### `browser_press`

参数：

- `session_id`
- `selector`
- `key`
- `page_id`：可选。

### `browser_hover`

参数：

- `session_id`
- `selector`
- `page_id`：可选。

### `browser_select_option`

参数：

- `session_id`
- `selector`：`<select>` 元素。
- `values`：可选；按 option 的 value 选择。
- `labels`：可选；按可见文本选择。`values` 与 `labels` 至少传一个。
- `page_id`：可选。

返回实际选中的 value 列表。

### `browser_set_input_files`

参数：

- `session_id`
- `selector`：`<input type=file>`。
- `files`：本地文件路径数组（支持 `~` 展开）；传空数组清空。
- `page_id`：可选。

### `browser_check` / `browser_uncheck`

参数：

- `session_id`
- `selector`：checkbox 或 radio。
- `page_id`：可选。

### `browser_reload`

参数：

- `session_id`
- `page_id`：可选。

返回刷新后的 URL、标题和响应状态。

### `browser_go_back`

参数：

- `session_id`
- `page_id`：可选。

### `browser_go_forward`

参数：

- `session_id`
- `page_id`：可选。

### `browser_wait_for_selector`

参数：

- `session_id`
- `selector`
- `page_id`：可选。
- `state`：`attached`、`detached`、`visible`、`hidden`。
- `timeout_ms`：可选。

### `browser_evaluate`

参数：

- `session_id`
- `script`
- `arg`：可选。
- `page_id`：可选。

返回 JavaScript 执行结果。结果不可 JSON 序列化时会转为字符串表示。

### `browser_get_text`

参数：

- `session_id`
- `selector`：可选；默认读取 `body`。
- `page_id`：可选。

### `browser_get_html`

参数：

- `session_id`
- `page_id`：可选。

### `browser_get_attribute`

参数：

- `session_id`
- `selector`
- `name`：属性名，如 `href`、`src`、`value`。
- `page_id`：可选。

元素不存在该属性时返回 `value: null`。

### `browser_is_visible` / `browser_is_enabled`

参数：

- `session_id`
- `selector`
- `page_id`：可选。

返回元素当前可见 / 可交互状态（立即判断，不等待）。

### `browser_count`

参数：

- `session_id`
- `selector`
- `page_id`：可选。

返回匹配该 selector 的元素数量，可用于判断列表项是否加载。

### `browser_screenshot`

参数：

- `session_id`
- `page_id`：可选。
- `options.path`：可选；不传则返回 base64。
- `options.full_page`
- `options.type`：`png` 或 `jpeg`。
- `options.quality`
- `options.omit_background`

## State Tools

### `browser_get_cookies`

参数：

- `session_id`
- `urls`：可选 URL 数组。

### `browser_add_cookies`

参数：

- `session_id`
- `cookies`：Playwright cookie 对象数组。

### `browser_clear_cookies`

参数：

- `session_id`

### `browser_storage_state`

参数：

- `session_id`
- `path`：可选；传入时保存到文件，同时返回 state。

## 错误码

- `BROWSER_LAUNCH_FAILED`：浏览器启动失败。
- `CDP_NOT_READY`：CDP 端口未在超时内可用。
- `SESSION_NOT_FOUND`：session_id 无效或会话已关闭。
- `PAGE_NOT_FOUND`：page_id 无效。
- `INVALID_JSON` / `INVALID_JSON_OBJECT`：参数 JSON 格式错误。
- `UNEXPECTED_ERROR`：未分类异常，查看 details。

## 上游能力映射

- `launch_context_async()`：`browser_launch mode=context`。
- `launch_persistent_context_async()`：`browser_launch mode=persistent`。
- `launch_async()`：`browser_launch mode=browser`。
- `extension_paths`、`humanize`、`geoip`、`backend`、`proxy`、`timezone`、`locale`：
  `LaunchOptions` 同名或近似同名字段。
- fingerprint flags：`fingerprint_seed`、`fingerprint_platform`、`fingerprint_args`、
  `extra_args`。
- CDP：`browser_start_cdp`。
