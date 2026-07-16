"""Tests for freshness check."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from healthchecker.checks.freshness import FreshnessCheck
from healthchecker.config import Settings
from healthchecker.models import CheckStatus


def test_freshness_ok() -> None:
    conn = MagicMock()
    recent = datetime.now(UTC) - timedelta(minutes=2)
    conn.execute.return_value.fetchone.return_value = (recent,)
    check = FreshnessCheck(Settings(), connection=conn)
    result = check.check()
    assert result.status == CheckStatus.OK


def test_freshness_critical_when_stale() -> None:
    conn = MagicMock()
    stale = datetime.now(UTC) - timedelta(minutes=20)
    conn.execute.return_value.fetchone.return_value = (stale,)
    check = FreshnessCheck(Settings(), connection=conn)
    result = check.check()
    assert result.status == CheckStatus.CRITICAL
