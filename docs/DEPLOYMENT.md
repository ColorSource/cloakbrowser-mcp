# Deployment

## Local stdio

适合 MCP Host 本地调用：

```bash
uvx cloakbrowser-mcp
```

源码：

```bash
uv run cloakbrowser-mcp
```

## Streamable HTTP

```bash
cloakbrowser-mcp serve --transport streamable-http --host 127.0.0.1 --port 8000 --path /mcp
```

Host URL：

```text
http://127.0.0.1:8000/mcp
```

## Docker Compose

```bash
docker compose up --build
```

默认：

- MCP HTTP endpoint：`http://127.0.0.1:8000/mcp`
- profile volume：`cloakbrowser_profiles`
- Xvfb：`:99`

## Docker Run

```bash
docker build -t cloakbrowser-mcp .
docker run --rm -p 127.0.0.1:8000:8000 cloakbrowser-mcp
```

带 profile 持久化：

```bash
docker run --rm \
  -p 127.0.0.1:8000:8000 \
  -v cloakbrowser_profiles:/profiles \
  cloakbrowser-mcp
```

## Headed Mode In Docker

设置：

```bash
CLOAKBROWSER_MCP_HEADLESS=false
```

镜像会启动 Xvfb。entrypoint 会清理上游 issue #283 暴露的 stale lock：

- `/tmp/.X99-lock`
- `/tmp/.X11-unix/X99`

## Kubernetes / containerd

显式绑定所有接口：

```yaml
args:
  - cloakbrowser-mcp
  - serve
  - --transport
  - streamable-http
  - --host
  - 0.0.0.0
  - --port
  - "8000"
  - --path
  - /mcp
```

Service 只暴露 MCP HTTP 端口。CDP 端口只在确实需要外部框架接管时开放。

## Security

- MCP 工具能浏览网页、读取页面内容、执行 JS、访问 cookies/storage。
- CDP 能完全控制浏览器。
- 不要把 MCP 或 CDP 直接暴露到公网。
- profile volume 可能包含登录态、cookies、localStorage。
- 生产环境应通过本地 loopback、VPN、反向代理认证或私有网络访问。

## Healthcheck

容器内：

```bash
cloakbrowser-mcp healthcheck
```

更完整：

```bash
cloakbrowser-mcp healthcheck --install-browser --probe-browser --check-docker
cloakbrowser-mcp selftest
```

## Upgrades

```bash
docker compose build --pull
docker compose up -d
docker compose exec cloakbrowser-mcp cloakbrowser-mcp healthcheck --probe-browser
```

升级后同步阅读上游 README、CHANGELOG、Dockerfile 和相关 issues。
