"""日志初始化。"""

from __future__ import annotations

import logging as py_logging
from pathlib import Path


def configure_logging(level: str = "INFO", log_file: str | None = None) -> None:
    handlers: list[py_logging.Handler] = [py_logging.StreamHandler()]
    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(py_logging.FileHandler(path, encoding="utf-8"))

    py_logging.basicConfig(
        level=getattr(py_logging, level.upper(), py_logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
        force=True,
    )
