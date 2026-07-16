"""Tests for partition helpers."""

from datetime import date

from lib.partitions import (
    create_partition_sql,
    parse_partition_date,
    partition_name,
    partitions_to_create,
    should_drop_partition,
)


def test_partition_name_format() -> None:
    assert partition_name(date(2026, 7, 16)) == "recentchange_20260716"


def test_partitions_to_create_includes_today_and_ahead() -> None:
    today = date(2026, 7, 16)
    days = partitions_to_create(today, days_ahead=3)
    assert days == [date(2026, 7, 16), date(2026, 7, 17), date(2026, 7, 18), date(2026, 7, 19)]


def test_parse_partition_date() -> None:
    assert parse_partition_date("recentchange_20260716") == date(2026, 7, 16)
    assert parse_partition_date("recentchange_default") is None


def test_should_drop_partition_respects_retention() -> None:
    today = date(2026, 7, 16)
    assert should_drop_partition(date(2026, 7, 1), today, retention_days=14) is True
    assert should_drop_partition(date(2026, 7, 10), today, retention_days=14) is False


def test_create_partition_sql_contains_bounds() -> None:
    sql = create_partition_sql(date(2026, 7, 16))
    assert "recentchange_20260716" in sql
    assert "2026-07-16" in sql
    assert "2026-07-17" in sql
