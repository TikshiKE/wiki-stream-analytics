"""Background check runner."""

from __future__ import annotations

from collections.abc import Callable

import structlog

from healthchecker.alerter import Alerter
from healthchecker.checks.base import HealthCheck
from healthchecker.config import Settings
from healthchecker.models import AggregatedHealth, CheckResult

log = structlog.get_logger(__name__)


class CheckRunner:
    def __init__(
        self,
        checks: list[HealthCheck],
        alerter: Alerter,
        settings: Settings,
        on_update: Callable[[AggregatedHealth], None] | None = None,
    ) -> None:
        self._checks = checks
        self._alerter = alerter
        self._settings = settings
        self._on_update = on_update
        self._latest = AggregatedHealth(status=AggregatedHealth.aggregate({}), checks={})

    @property
    def latest(self) -> AggregatedHealth:
        return self._latest

    def run_once(self) -> AggregatedHealth:
        results: dict[str, CheckResult] = {}
        for check in self._checks:
            try:
                result = check.check()
            except Exception as exc:
                log.exception("check_failed", check=check.name, error=str(exc))
                from healthchecker.models import CheckStatus

                result = CheckResult(CheckStatus.CRITICAL, {"error": str(exc)})
            results[check.name] = result
            self._alerter.process(check.name, result)
            log.info(
                "check_complete",
                check=check.name,
                status=result.status.value,
                details=result.details,
            )

        aggregated = AggregatedHealth(
            status=AggregatedHealth.aggregate(results),
            checks=results,
        )
        self._latest = aggregated
        if self._on_update:
            self._on_update(aggregated)
        return aggregated

    def loop(self, stop_event) -> None:
        log.info("check_loop_started", interval_s=self._settings.check_interval_seconds)
        while not stop_event.is_set():
            self.run_once()
            stop_event.wait(self._settings.check_interval_seconds)
