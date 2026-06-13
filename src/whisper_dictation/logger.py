"""Rotating file + stderr logger for whisper-dictation."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def log_path() -> Path:
    from . import config as cfg
    return cfg.app_dir() / "app.log"


def _setup_root_logger() -> None:
    root = logging.getLogger("whisper_dictation")
    if root.handlers:
        return

    level = logging.DEBUG if os.environ.get("WHISPER_DEBUG") == "1" else logging.INFO
    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    try:
        fh = RotatingFileHandler(
            log_path(), maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception:
        pass

    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    root.addHandler(sh)


_setup_root_logger()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
