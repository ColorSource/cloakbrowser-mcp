# Basic Agent Flow

Agent 连接 MCP 后：

1. 调用 `cloakbrowser_healthcheck`。
2. 调用 `browser_launch`：

```json
{
  "options": {
    "mode": "context",
    "headless": true
  }
}
```

3. 从返回值取 `session.session_id`。
4. 调用 `browser_navigate`：

```json
{
  "session_id": "session-...",
  "url": "https://example.com"
}
```

5. 调用 `browser_get_text` 或 `browser_screenshot`。
6. 调用 `browser_close`：

```json
{
  "session_id": "session-..."
}
```

持久 profile：

```json
{
  "options": {
    "mode": "persistent",
    "profile_name": "returning-user",
    "headless": false,
    "humanize": true
  }
}
```
