"""Data quality check helpers for the maintenance DAG."""

from __future__ import annotations

from datetime import datetime, timedelta


def evaluate_freshness(
    max_event_ts: datetime | None,
    now: datetime,
    max_age_minutes: int = 10,
) -> tuple[bool, str]:
    if max_event_ts is None:
        return False, "no rows in raw.recentchange"
    # Normalize timezones for comparison
    if max_event_ts.tzinfo is None:
        max_event_ts = max_event_ts.replace(tzinfo=now.tzinfo)
    age = now - max_event_ts
    if age > timedelta(minutes=max_age_minutes):
        minutes = age.total_seconds() / 60
        return False, f"raw data stale: last event {minutes:.1f} minutes ago"
    return True, "freshness ok"


def evaluate_volume(
    yesterday_count: int | None,
    avg_prior_7d: float | None,
    tolerance: float = 0.6,
) -> tuple[bool, str]:
    """Check yesterday's volume is within ±tolerance of the 7-day average."""
    if yesterday_count is None:
        return True, "no yesterday data yet — skipped"
    if avg_prior_7d is None or avg_prior_7d <= 0:
        return True, "insufficient history for volume baseline — skipped"
    ratio = yesterday_count / avg_prior_7d
    lower = 1 - tolerance
    upper = 1 + tolerance
    if ratio < lower or ratio > upper:
        return (
            False,
            f"yesterday volume {yesterday_count} vs 7d avg {avg_prior_7d:.0f} "
            f"(ratio {ratio:.2f}, allowed {lower:.1f}–{upper:.1f})",
        )
    return True, "volume ok"
