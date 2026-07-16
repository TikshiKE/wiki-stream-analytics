"""Tests for dashboard health check."""

import urllib.error
from unittest.mock import MagicMock

from healthchecker.checks.dashboard import DashboardCheck
from healthchecker.config import Settings
from healthchecker.models import CheckStatus


def test_dashboard_ok() -> None:
    response = MagicMock()
    response.status = 200
    response.read.return_value = b"ok"
    opener = MagicMock()
    opener.open.return_value = response
    check = DashboardCheck(Settings(dashboard_url="http://dashboard:8501"), opener=opener)
    assert check.check().status == CheckStatus.OK


def test_dashboard_critical_on_failure() -> None:
    opener = MagicMock()
    opener.open.side_effect = urllib.error.URLError("connection refused")
    check = DashboardCheck(Settings(), opener=opener)
    assert check.check().status == CheckStatus.CRITICAL
