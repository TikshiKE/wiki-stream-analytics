"""Tests for DQ evaluation helpers."""

from datetime import UTC, datetime, timedelta

from lib.dq import evaluate_freshness, evaluate_volume


def test_freshness_ok_for_recent_data() -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
    max_ts = now - timedelta(minutes=5)
    ok, msg = evaluate_freshness(max_ts, now, max_age_minutes=10)
    assert ok is True
    assert "ok" in msg


def test_freshness_fails_when_stale() -> None:
    now = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
    max_ts = now - timedelta(minutes=20)
    ok, msg = evaluate_freshness(max_ts, now, max_age_minutes=10)
    assert ok is False
    assert "stale" in msg.lower()


def test_volume_ok_within_tolerance() -> None:
    ok, _ = evaluate_volume(1000, 900.0, tolerance=0.6)
    assert ok is True


def test_volume_fails_outside_tolerance() -> None:
    ok, msg = evaluate_volume(100, 1000.0, tolerance=0.6)
    assert ok is False
    assert "ratio" in msg


def test_volume_skips_without_yesterday() -> None:
    ok, msg = evaluate_volume(None, 1000.0, tolerance=0.6)
    assert ok is True
    assert "skipped" in msg


def test_volume_skips_without_baseline() -> None:
    ok, msg = evaluate_volume(100, None, tolerance=0.6)
    assert ok is True
    assert "skipped" in msg
