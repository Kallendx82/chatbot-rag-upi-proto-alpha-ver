"""Centralised logging configuration.

Logs to BOTH the console and a rotating file (backend/logs/backend.log) so
unhandled errors / tracebacks are persisted for later diagnosis instead of
scrolling off the terminal. Call setup_logging() once at application startup;
use get_logger(__name__) everywhere else.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_CONFIGURED = False

# backend/app/core/logging.py -> parents[2] == backend/ ; keep logs there so the
# path is stable regardless of the process working directory.
# Write logs OUTSIDE the backend package dir. uvicorn --reload watches the
# backend/ directory, so a log file under backend/ would retrigger a reload on
# every write -> the server restarts mid-request -> /chat returns HTTP 500
# ("socket hang up"). parents[3] = ".../Source code", a sibling of backend/.
_LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
_LOG_FILE = _LOG_DIR / "backend.log"


def setup_logging(level: str = "INFO") -> None:
    """Configure root logging once. Safe to call multiple times."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (as before).
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    handlers: list[logging.Handler] = [console]

    # Rotating file handler: persists tracebacks to backend/logs/backend.log.
    # 2 MB per file, keep 5 backups. Never let logging break app startup.
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            _LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        handlers.append(file_handler)
    except Exception as exc:  # noqa: BLE001 - logging must never crash the app
        console.handle(logging.makeLogRecord({
            "levelname": "WARNING", "name": __name__,
            "msg": f"Could not open log file {_LOG_FILE}: {exc}",
        }))

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Replace any pre-existing handlers (e.g. uvicorn's) for consistent format.
    root.handlers = handlers

    # Quiet down noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True
    logging.getLogger(__name__).info("Logging to console + file: %s", _LOG_FILE)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name)
