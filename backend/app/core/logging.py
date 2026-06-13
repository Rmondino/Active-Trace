"""Structured JSON logging for activia-trace.

Configures the root logger to emit one JSON object per line,
parseable by any log aggregator (Datadog, Loki, CloudWatch, etc.).
Never emits secrets or PII in plain text.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as single-line JSON.

    Each record includes at minimum:
        - timestamp: ISO-8601 in UTC
        - level: log level name
        - message: the log message
        - logger: the logger name

    Extra fields passed in the `extra` dict are included as top-level keys.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include any extra context passed to the logger
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "levelname", "levelno", "lineno",
                "message", "module", "msecs", "msg", "name", "pathname",
                "process", "processName", "relativeCreated", "stack_info",
                "thread", "threadName",
            ):
                log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


def configure_json_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with JSON output to stdout.

    Args:
        level: Logging level (default: INFO).
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    # Remove existing handlers to avoid duplicate output
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
