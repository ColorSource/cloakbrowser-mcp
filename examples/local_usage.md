# Local Usage

```bash
uv sync
uv run cloakbrowser-mcp healthcheck --install-browser
uv run cloakbrowser-mcp
```

源码目录 MCP Host 配置：

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

首次连接后调用：

1. `cloakbrowser_healthcheck`
2. `browser_launch`
3. `browser_navigate`
4. `browser_get_text`
5. `browser_close`
