"""Streamlit dashboard health endpoint check."""

from __future__ import annotations

import urllib.error
import urllib.request

from healthchecker.checks.base import HealthCheck
from healthchecker.config import Settings
from healthchecker.models import CheckResult, CheckStatus


class DashboardCheck(HealthCheck):
    def __init__(self, settings: Settings, opener=None) -> None:
        self._settings = settings
        self._opener = opener

    @property
    def name(self) -> str:
        return "dashboard"

    def check(self) -> CheckResult:
        url = f"{self._settings.dashboard_url.rstrip('/')}/_stcore/health"
        try:
            if self._opener is not None:
                response = self._opener.open(url, timeout=5)
            else:
                response = urllib.request.urlopen(url, timeout=5)
            body = response.read().decode().strip()
            status_code = response.status
        except urllib.error.URLError as exc:
            return CheckResult(CheckStatus.CRITICAL, {"url": url, "error": str(exc)})

        details = {"url": url, "status_code": status_code, "body": body}
        if status_code != 200 or body.lower() != "ok":
            return CheckResult(CheckStatus.CRITICAL, details)
        return CheckResult(CheckStatus.OK, details)
