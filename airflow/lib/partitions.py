"""Partition name/bounds helpers and SQL generation for raw.recentchange."""

from __future__ import annotations

from datetime import date, timedelta


def partition_name(day: date) -> str:
    return f"recentchange_{day.strftime('%Y%m%d')}"


def partition_bounds(day: date) -> tuple[date, date]:
    return day, day + timedelta(days=1)


def create_partition_sql(day: date) -> str:
    name = partition_name(day)
    start, end = partition_bounds(day)
    return (
        f"CREATE TABLE IF NOT EXISTS raw.{name} "
        f"PARTITION OF raw.recentchange "
        f"FOR VALUES FROM ('{start.isoformat()}'::timestamptz) "
        f"TO ('{end.isoformat()}'::timestamptz);"
    )


def partitions_to_create(today: date, days_ahead: int = 3) -> list[date]:
    """Return dates for today .. today+days_ahead inclusive."""
    return [today + timedelta(days=i) for i in range(days_ahead + 1)]


def parse_partition_date(table_name: str) -> date | None:
    """Parse YYYYMMDD from raw.recentchange_YYYYMMDD; ignore default partition."""
    prefix = "recentchange_"
    if not table_name.startswith(prefix) or table_name == "recentchange_default":
        return None
    suffix = table_name.removeprefix(prefix)
    if len(suffix) != 8 or not suffix.isdigit():
        return None
    return date(int(suffix[:4]), int(suffix[4:6]), int(suffix[6:8]))


def should_drop_partition(partition_day: date, today: date, retention_days: int) -> bool:
    """Drop partitions strictly older than the retention window."""
    cutoff = today - timedelta(days=retention_days)
    return partition_day < cutoff


def drop_partition_sql(day: date) -> str:
    return f"DROP TABLE IF EXISTS raw.{partition_name(day)};"
