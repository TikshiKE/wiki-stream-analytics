"""Healthchecker entrypoint."""

from __future__ import annotations

import logging
import signal
import threading

import redis
import structlog
import uvicorn

from healthchecker.alerter import Alerter
from healthchecker.app import create_app
from healthchecker.checks import build_checks
from healthchecker.config import Settings
from healthchecker.runner import CheckRunner
from healthchecker.state_store import RedisStateStore


def setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )


def run() -> None:
    setup_logging()
    settings = Settings()
    log = structlog.get_logger(__name__)

    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    store = RedisStateStore(redis_client)
    alerter = Alerter(settings, store)
    checks = build_checks(settings)
    runner = CheckRunner(checks, alerter, settings)
    runner.run_once()

    stop_event = threading.Event()

    def _handle_signal(signum, frame) -> None:
        log.info("shutdown_signal", signum=signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    thread = threading.Thread(target=runner.loop, args=(stop_event,), daemon=True)
    thread.start()

    app = create_app(runner)
    uvicorn.run(
        app,
        host=settings.health_host,
        port=settings.health_port,
        log_level="info",
    )
