"""配置加载与环境变量映射。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

import tomllib
from pydantic import BaseModel, Field, field_validator

Transport = Literal["stdio", "sse", "streamable-http"]
LaunchMode = Literal["browser", "context", "persistent"]
Backend = Literal["playwright", "patchright"]


class ServerSettings(BaseModel):
    name: str = "cloakbrowser-mcp"
    transport: Transport = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"
    stateless_http: bool = True
    json_response: bool = True


class BrowserSettings(BaseModel):
    launch_mode: LaunchMode = "context"
    headless: bool = True
    proxy: str | dict[str, Any] | None = None
    geoip: bool = False
    timezone: str | None = None
    locale: str | None = None
    geolocation: dict[str, float] | None = None
    fingerprint_seed: str | int | None = None
    fingerprint_platform: str | None = None
    fingerprint_args: dict[str, str | int | float | bool] = Field(default_factory=dict)
    extra_args: list[str] = Field(default_factory=list)
    stealth_args: bool = True
    backend: Backend = "playwright"
    humanize: bool = False
    human_preset: Literal["default", "careful"] = "default"
    human_config: dict[str, Any] | None = None
    profile_root: Path = Path(".cloakbrowser-mcp/profiles")
    profile_name: str = "default"
    user_data_dir: Path | None = None
    persistent_session: bool = False
    extension_paths: list[str] = Field(default_factory=list)
    user_agent: str | None = None
    viewport: dict[str, int] | None = None
    no_viewport: bool = False
    color_scheme: Literal["light", "dark", "no-preference"] | None = None
    context_kwargs: dict[str, Any] = Field(default_factory=dict)
    launch_kwargs: dict[str, Any] = Field(default_factory=dict)

    @field_validator("profile_root", "user_data_dir", mode="before")
    @classmethod
    def _expand_path(cls, value: Any) -> Any:
        if value in (None, ""):
            return None
        return Path(str(value)).expanduser()


class CdpSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int | None = None
    expose_host: str = "127.0.0.1"
    timeout_seconds: float = 10.0


class RuntimeSettings(BaseModel):
    timeout_ms: int = 30000
    retries: int = 0
    install_browser_on_start: bool = False
    healthcheck_probe_browser: bool = False
    check_docker: bool = False
    check_node: bool = True
    log_level: str = "INFO"
    log_file: str | None = None


class Settings(BaseModel):
    server: ServerSettings = Field(default_factory=ServerSettings)
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
    cdp: CdpSettings = Field(default_factory=CdpSettings)
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)


ENV_MAP: dict[str, tuple[str, ...]] = {
    "CLOAKBROWSER_MCP_TRANSPORT": ("server", "transport"),
    "CLOAKBROWSER_MCP_HOST": ("server", "host"),
    "CLOAKBROWSER_MCP_PORT": ("server", "port"),
    "CLOAKBROWSER_MCP_PATH": ("server", "path"),
    "CLOAKBROWSER_MCP_STATELESS_HTTP": ("server", "stateless_http"),
    "CLOAKBROWSER_MCP_JSON_RESPONSE": ("server", "json_response"),
    "CLOAKBROWSER_MCP_LAUNCH_MODE": ("browser", "launch_mode"),
    "CLOAKBROWSER_MCP_HEADLESS": ("browser", "headless"),
    "CLOAKBROWSER_MCP_PROXY": ("browser", "proxy"),
    "CLOAKBROWSER_MCP_GEOIP": ("browser", "geoip"),
    "CLOAKBROWSER_MCP_TIMEZONE": ("browser", "timezone"),
    "CLOAKBROWSER_MCP_LOCALE": ("browser", "locale"),
    "CLOAKBROWSER_MCP_GEOLOCATION": ("browser", "geolocation"),
    "CLOAKBROWSER_MCP_FINGERPRINT_SEED": ("browser", "fingerprint_seed"),
    "CLOAKBROWSER_MCP_FINGERPRINT_PLATFORM": ("browser", "fingerprint_platform"),
    "CLOAKBROWSER_MCP_FINGERPRINT_ARGS": ("browser", "fingerprint_args"),
    "CLOAKBROWSER_MCP_EXTRA_ARGS": ("browser", "extra_args"),
    "CLOAKBROWSER_MCP_STEALTH_ARGS": ("browser", "stealth_args"),
    "CLOAKBROWSER_MCP_BACKEND": ("browser", "backend"),
    "CLOAKBROWSER_MCP_HUMANIZE": ("browser", "humanize"),
    "CLOAKBROWSER_MCP_HUMAN_PRESET": ("browser", "human_preset"),
    "CLOAKBROWSER_MCP_HUMAN_CONFIG": ("browser", "human_config"),
    "CLOAKBROWSER_MCP_PROFILE_ROOT": ("browser", "profile_root"),
    "CLOAKBROWSER_MCP_PROFILE_NAME": ("browser", "profile_name"),
    "CLOAKBROWSER_MCP_USER_DATA_DIR": ("browser", "user_data_dir"),
    "CLOAKBROWSER_MCP_PERSISTENT_SESSION": ("browser", "persistent_session"),
    "CLOAKBROWSER_MCP_EXTENSION_PATHS": ("browser", "extension_paths"),
    "CLOAKBROWSER_MCP_USER_AGENT": ("browser", "user_agent"),
    "CLOAKBROWSER_MCP_VIEWPORT": ("browser", "viewport"),
    "CLOAKBROWSER_MCP_NO_VIEWPORT": ("browser", "no_viewport"),
    "CLOAKBROWSER_MCP_COLOR_SCHEME": ("browser", "color_scheme"),
    "CLOAKBROWSER_MCP_CONTEXT_KWARGS": ("browser", "context_kwargs"),
    "CLOAKBROWSER_MCP_LAUNCH_KWARGS": ("browser", "launch_kwargs"),
    "CLOAKBROWSER_MCP_CDP_HOST": ("cdp", "host"),
    "CLOAKBROWSER_MCP_CDP_PORT": ("cdp", "port"),
    "CLOAKBROWSER_MCP_CDP_EXPOSE_HOST": ("cdp", "expose_host"),
    "CLOAKBROWSER_MCP_CDP_TIMEOUT_SECONDS": ("cdp", "timeout_seconds"),
    "CLOAKBROWSER_MCP_TIMEOUT_MS": ("runtime", "timeout_ms"),
    "CLOAKBROWSER_MCP_RETRIES": ("runtime", "retries"),
    "CLOAKBROWSER_MCP_INSTALL_BROWSER_ON_START": ("runtime", "install_browser_on_start"),
    "CLOAKBROWSER_MCP_HEALTHCHECK_PROBE_BROWSER": ("runtime", "healthcheck_probe_browser"),
    "CLOAKBROWSER_MCP_CHECK_DOCKER": ("runtime", "check_docker"),
    "CLOAKBROWSER_MCP_CHECK_NODE": ("runtime", "check_node"),
    "CLOAKBROWSER_MCP_LOG_LEVEL": ("runtime", "log_level"),
    "CLOAKBROWSER_MCP_LOG_FILE": ("runtime", "log_file"),
}


def load_settings(config_path: str | os.PathLike[str] | None = None) -> Settings:
    _load_dotenv()

    data: dict[str, Any] = {}
    raw_path = (
        str(config_path)
        if config_path
        else os.environ.get("CLOAKBROWSER_MCP_CONFIG")
        or os.environ.get("CLOAKBROWSER_MCP_CONFIG_FILE")
    )
    if raw_path:
        data = _load_config_file(Path(raw_path))

    env_data: dict[str, Any] = {}
    for env_name, target_path in ENV_MAP.items():
        if env_name not in os.environ:
            continue
        _assign_nested(env_data, target_path, _parse_env_value(os.environ[env_name]))

    merged = _deep_merge(data, env_data)
    return Settings.model_validate(merged)


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(override=False)


def _load_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if suffix in {".toml", ".tml"}:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    raise ValueError("仅支持 JSON 或 TOML 配置文件")


def _parse_env_value(raw: str) -> Any:
    value = raw.strip()
    lowered = value.lower()
    if lowered in {"true", "1", "yes", "y", "on"}:
        return True
    if lowered in {"false", "0", "no", "n", "off"}:
        return False
    if lowered in {"none", "null", ""}:
        return None
    if value.startswith(("{", "[")):
        return json.loads(value)
    if "," in value:
        return [part.strip() for part in value.split(",") if part.strip()]
    return value


def _assign_nested(data: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    cursor = data
    for key in path[:-1]:
        cursor = cursor.setdefault(key, {})
    cursor[path[-1]] = value


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def settings_for_display(settings: Settings) -> dict[str, Any]:
    data = settings.model_dump(mode="json")
    proxy = data.get("browser", {}).get("proxy")
    if isinstance(proxy, str) and "@" in proxy:
        data["browser"]["proxy"] = _redact_proxy(proxy)
    elif isinstance(proxy, dict) and proxy.get("password"):
        data["browser"]["proxy"] = {**proxy, "password": "***"}
    return data


def _redact_proxy(proxy: str) -> str:
    scheme, rest = proxy.split("://", 1) if "://" in proxy else ("", proxy)
    if "@" not in rest:
        return proxy
    _, host = rest.rsplit("@", 1)
    return f"{scheme}://***:***@{host}" if scheme else f"***:***@{host}"
