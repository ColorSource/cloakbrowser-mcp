"""通用 JSON 结果和错误工具。"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class ToolFailure(Exception):
    """可返回给 MCP 调用方的结构化错误。"""

    def __init__(
        self,
        error_code: str,
        message: str,
        suggested_fix: str,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.suggested_fix = suggested_fix
        self.details = dict(details or {})


def ok(data: Mapping[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": True}
    if data:
        payload.update(data)
    payload.update(extra)
    return make_jsonable(payload)


def fail(
    error_code: str,
    message: str,
    suggested_fix: str,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return make_jsonable(
        {
            "ok": False,
            "error": {
                "error_code": error_code,
                "message": message,
                "suggested_fix": suggested_fix,
                "details": dict(details or {}),
            },
        }
    )


def fail_from_exception(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, ToolFailure):
        return fail(exc.error_code, exc.message, exc.suggested_fix, exc.details)
    return fail(
        "UNEXPECTED_ERROR",
        str(exc) or exc.__class__.__name__,
        "读取返回的 details；如果是启动失败，先调用 cloakbrowser_healthcheck。若问题来自上游浏览器行为，重新阅读上游 README、examples 和相关 issues。",
        {"type": exc.__class__.__name__},
    )


def make_jsonable(value: Any) -> Any:
    """把 Playwright/CloakBrowser 返回值转换成 MCP 可序列化对象。"""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, Mapping):
            return {str(k): make_jsonable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [make_jsonable(v) for v in value]
        return repr(value)


def parse_json_object(raw: str | None, field_name: str) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolFailure(
            "INVALID_JSON",
            f"{field_name} 不是合法 JSON: {exc}",
            f"把 {field_name} 改成 JSON 对象，例如 {{\"key\":\"value\"}}。",
        ) from exc
    if not isinstance(value, dict):
        raise ToolFailure(
            "INVALID_JSON_OBJECT",
            f"{field_name} 必须是 JSON 对象。",
            f"把 {field_name} 改成 JSON 对象，而不是数组或字符串。",
        )
    return value
