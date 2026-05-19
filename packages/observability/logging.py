import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


def _service_name() -> str:
    return os.environ.get("DD_SERVICE", "invoice-api")


def _env_name() -> str:
    return os.environ.get("DD_ENV", "local")


def _version_name() -> str:
    return os.environ.get("DD_VERSION", "local")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "logger": record.name,
            "service": _service_name(),
            "env": _env_name(),
            "version": _version_name(),
        }
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            payload.update(record.extra_fields)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    level: str,
    message: str,
    **fields: Any,
) -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)
    record = logger.makeRecord(
        logger.name,
        log_level,
        "(observability)",
        0,
        message,
        (),
        None,
    )
    record.extra_fields = fields
    logger.handle(record)
