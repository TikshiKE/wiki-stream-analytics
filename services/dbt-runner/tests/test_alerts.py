"""Tests for dbt-runner alert helper."""

import logging

from alerts import send_telegram_alert


def test_telegram_skipped_without_token(monkeypatch, caplog):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    with caplog.at_level(logging.WARNING):
        send_telegram_alert("test failure")
    assert "telegram_not_configured" in caplog.text
