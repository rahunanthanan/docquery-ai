"""Structured JSON logging via structlog (requirements §9).

Every log line is a single JSON object on stdout (container-friendly).
The request-context middleware in `app.main` binds `request_id` for the
duration of each request; auth (Task 3) will additionally bind `user_id`.
"""

import logging

import structlog


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )
