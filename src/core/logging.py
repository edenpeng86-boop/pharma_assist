"""Application logging setup."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from src.core.config import ROOT_DIR, config


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """Configure console and rotating file logs once."""
    log_cfg = config.get("logging", {})
    level_name = str(log_cfg.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    log_dir = ROOT_DIR / log_cfg.get("dir", "logs")
    log_file = log_dir / log_cfg.get("file", "pharmassist.log")
    max_bytes = int(log_cfg.get("max_bytes", 2_000_000))
    backup_count = int(log_cfg.get("backup_count", 3))

    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    if not any(getattr(handler, "_pharmassist_console", False) for handler in root.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        console_handler._pharmassist_console = True
        root.addHandler(console_handler)

    if not any(getattr(handler, "_pharmassist_file", False) for handler in root.handlers):
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        file_handler._pharmassist_file = True
        root.addHandler(file_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
