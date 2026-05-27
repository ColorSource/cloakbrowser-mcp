# CloakBrowser MCP

> **AI Agent Start Here / AI 读我**  
> 如果你是 AI Agent，请优先阅读：[`docs/AI_AGENT_GUIDE.md`](docs/AI_AGENT_GUIDE.md)

CloakBrowser MCP 是基于上游 [CloakBrowser](https://github.com/CloakHQ/CloakBrowser)
的 MCP Server。它把 CloakBrowser 的 stealth Chromium、Playwright 会话、持久
profile、proxy、GeoIP、fingerprint、humanize、extension、CDP 和诊断能力封装成
AI Agent 可直接调用的 MCP 工具。

本仓库不分发 CloakBrowser 浏览器补丁本身。浏览器二进制、指纹补丁和底层启动逻辑
以 CloakBrowser 上游为事实来源；本项目负责 MCP 封装、配置、文档、健康检查和容器化。

## Quick Start

本地最快路径：

```bash
uvx cloakbrowser-mcp healthcheck --install-browser
uvx cloakbrowser-mcp
```

默认启动 `stdio` MCP transport，适合 Claude Desktop、Cursor、VS Code 等 MCP Host。
如果本包尚未发布到 PyPI，把命令改成：

```bash
uvx --from git+<this-repo-url> cloakbrowser-mcp healthcheck --install-browser
uvx --from git+<this-repo-url> cloakbrowser-mcp
```

从源码运行：

```bash
git clone <this-repo-url>
cd cloakbrowser-mcp
uv sync
uv run cloakbrowser-mcp healthcheck --install-browser
uv run cloakbrowser-mcp
```

## MCP Host 配置

stdio 配置示例：

```json
{
  "mcpServers": {
    "cloakbrowser": {
      "command": "uvx",
      "args": ["cloakbrowser-mcp"],
      "env": {
        "CLOAKBROWSER_MCP_HEADLESS": "true",
        "CLOAKBROWSER_MCP_GEOIP": "false"
      }
    }
  }
}
```

仓库内还有 Host 示例：

- [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json)
- [`examples/cursor_mcp_config.json`](examples/cursor_mcp_config.json)
- [`examples/vscode_mcp_config.json`](examples/vscode_mcp_config.json)

## Docker

```bash
docker compose up --build
```

默认以 `streamable-http` 暴露到 `127.0.0.1:8000/mcp`，并带 Xvfb、字体、健康检查和
profile volume。更多容器说明见 [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)。

## 安装后验证

```bash
cloakbrowser-mcp healthcheck --install-browser
cloakbrowser-mcp selftest
cloakbrowser-mcp tools-json
```

在 MCP Host 中连接后，先调用：

1. `cloakbrowser_healthcheck`
2. `browser_launch`
3. `browser_navigate`
4. `browser_close`

工具 schema 由 MCP Host 通过 `tools/list` 自动读取。命令行可用
`cloakbrowser-mcp tools-json` 查看工具目录；完整工具说明在
[`docs/TOOLS.md`](docs/TOOLS.md)。

## 配置

配置可来自环境变量、`.env`、JSON/TOML 配置文件和每次工具调用的 `options` 参数。
常用变量：

```bash
CLOAKBROWSER_MCP_HEADLESS=true
CLOAKBROWSER_MCP_PROXY=http://user:pass@host:port
CLOAKBROWSER_MCP_GEOIP=true
CLOAKBROWSER_MCP_TIMEZONE=America/New_York
CLOAKBROWSER_MCP_LOCALE=en-US
CLOAKBROWSER_MCP_HUMANIZE=true
CLOAKBROWSER_MCP_PROFILE_ROOT=.cloakbrowser-mcp/profiles
```

完整字段见 [`.env.example`](.env.example) 和
[`docs/CONFIGURATION.md`](docs/CONFIGURATION.md)。

## 与上游 CloakBrowser 的关系

本 MCP 当前参考上游 commit
`14ec2ebf5f952b3dcc8ee019965cc48cbf7ccf53`，对应 README 中的
`v0.3.31` / Chromium `146.0.7680.177.5` 说明。上游支持能力、配置坑和 issue
归纳见 [`docs/UPSTREAM_NOTES.md`](docs/UPSTREAM_NOTES.md)。

同步上游时：

```bash
pip install -U cloakbrowser
cloakbrowser-mcp healthcheck --install-browser --probe-browser
```

然后重新阅读上游 README、examples、Dockerfile、CHANGELOG 和与当前失败相关的 issues，
再更新 `docs/UPSTREAM_NOTES.md`、`docs/TOOLS.md` 和测试。

## 故障入口

- 安装或二进制下载失败：[`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)
- proxy / GeoIP / timezone / locale：[`docs/CONFIGURATION.md`](docs/CONFIGURATION.md)
- Docker / Xvfb / CDP：[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- 工具调用顺序：[`docs/AI_AGENT_GUIDE.md`](docs/AI_AGENT_GUIDE.md)

## License

MIT。CloakBrowser 上游也使用 MIT；浏览器二进制许可请以
[CloakBrowser upstream](https://github.com/CloakHQ/CloakBrowser) 为准。
