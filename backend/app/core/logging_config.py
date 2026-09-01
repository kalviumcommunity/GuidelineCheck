"""Structured logging configuration for GuidelineCheck."""
from __future__ import annotations

import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    root = logging.getLogger()
    if root.handlers:
        # Already configured (e.g. under pytest / reload) - avoid duplicate handlers.
        root.setLevel(settings.log_level)
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(settings.log_level)

    # Quiet down noisy third-party loggers a bit.
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
