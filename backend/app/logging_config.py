"""
Structured logging configuration.

In production, logs go to stdout where Kubernetes (and downstream tools like
Loki, CloudWatch, etc.) can collect them. JSON-formatted logs are machine-
parseable, which matters once you have more than one pod producing output.
"""

import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Formats log records as a single JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include exception info if present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Include any extra fields passed via logger.info("msg", extra={...})
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "message", "module",
                "msecs", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName", "taskName",
            }:
                payload[key] = value
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    """Set up root logger with JSON formatter writing to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers = [handler]  # replace any default handlers
    root.setLevel(level)