FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdbus-1-3 libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libx11-xcb1 libfontconfig1 libx11-6 \
    libxcb1 libxext6 libxshmfence1 libglib2.0-0 libgtk-3-0 \
    libpangocairo-1.0-0 libcairo-gobject2 libgdk-pixbuf-2.0-0 \
    libxss1 libxtst6 fonts-liberation fonts-noto-color-emoji \
    fonts-unifont fonts-freefont-ttf fonts-ipafont-gothic \
    fonts-wqy-zenhei fonts-tlwg-loma-otf xvfb curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
COPY docs/ docs/
COPY examples/ examples/
RUN pip install --no-cache-dir .

# 构建期预下载上游 Chromium。构建环境若无网络，可删除这一行并在运行期执行 install。
RUN cloakbrowser-mcp install

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV DISPLAY=:99 \
    CLOAKBROWSER_MCP_TRANSPORT=streamable-http \
    CLOAKBROWSER_MCP_HOST=0.0.0.0 \
    CLOAKBROWSER_MCP_PORT=8000 \
    CLOAKBROWSER_MCP_PATH=/mcp \
    CLOAKBROWSER_MCP_PROFILE_ROOT=/profiles \
    CLOAKBROWSER_MCP_HEADLESS=true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
  CMD cloakbrowser-mcp healthcheck || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["cloakbrowser-mcp", "serve", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000", "--path", "/mcp"]
