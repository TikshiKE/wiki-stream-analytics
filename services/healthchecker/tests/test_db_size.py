"""Tests for database size check."""

from unittest.mock import MagicMock

from healthchecker.checks.db_size import DbSizeCheck
from healthchecker.config import Settings
from healthchecker.models import CheckStatus


def test_db_size_ok() -> None:
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (1024**3,)
    check = DbSizeCheck(Settings(db_size_warn_bytes=10 * 1024**3), connection=conn)
    assert check.check().status == CheckStatus.OK


def test_db_size_warn() -> None:
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (11 * 1024**3,)
    check = DbSizeCheck(Settings(db_size_warn_bytes=10 * 1024**3), connection=conn)
    assert check.check().status == CheckStatus.WARN
