"""Centralised logging with per-request correlation id."""

import json
import logging
import sys
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO", json_logs: bool = False) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    if json_logs:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s: %(message)s")
        )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # uvicorn access log is replaced by our own request log middleware
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = False

def configure_logging(level: str = "INFO") -> None:
    setup_logging(level)