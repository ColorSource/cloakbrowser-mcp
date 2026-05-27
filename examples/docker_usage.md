# Docker Usage

```bash
docker compose up --build
```

MCP endpoint：

```text
http://127.0.0.1:8000/mcp
```

运行完整自检：

```bash
docker compose exec cloakbrowser-mcp cloakbrowser-mcp healthcheck --probe-browser
```

headed + proxy 示例：

```bash
CLOAKBROWSER_MCP_HEADLESS=false
CLOAKBROWSER_MCP_PROXY=http://user:pass@residential-proxy:port
CLOAKBROWSER_MCP_GEOIP=true
CLOAKBROWSER_MCP_HUMANIZE=true
docker compose up --build
```
