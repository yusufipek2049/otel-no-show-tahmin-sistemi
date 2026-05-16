from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlsplit


DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(*, level: str = "INFO") -> None:
    resolved_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(level=resolved_level, format=DEFAULT_LOG_FORMAT)
    else:
        root_logger.setLevel(resolved_level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(event: str, **fields: Any) -> str:
    parts = [event]
    for key, value in fields.items():
        parts.append(f"{key}={_format_log_value(value)}")
    return " ".join(parts)


def mask_database_url(database_url: str | None) -> str:
    if not database_url:
        return "not_configured"

    try:
        parsed = urlsplit(database_url)
    except ValueError:
        return "unparseable"

    host = parsed.hostname or "unknown_host"
    database_name = parsed.path.rsplit("/", maxsplit=1)[-1] if parsed.path else "unknown_database"
    port = f":{parsed.port}" if parsed.port else ""
    driver = parsed.scheme or "unknown_driver"
    return f"{driver}://{host}{port}/{database_name}"


def _format_log_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()

    text = str(value)
    if not text:
        return '""'
    if any(character.isspace() for character in text):
        return repr(text)
    return text
