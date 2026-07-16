"""Tests for alerter state transitions and throttling."""

from healthchecker.alerter import Alerter
from healthchecker.config import Settings
from healthchecker.models import CheckResult, CheckStatus
from healthchecker.state_store import InMemoryStateStore, should_send_alert


def test_should_send_alert_respects_throttle() -> None:
    assert should_send_alert(None, 1000.0, 1800) is True
    assert should_send_alert(1000.0, 2000.0, 1800) is False
    assert should_send_alert(1000.0, 3000.0, 1800) is True


def test_ok_to_problem_sends_alert() -> None:
    store = InMemoryStateStore()
    settings = Settings(telegram_bot_token="", telegram_chat_id="")
    alerter = Alerter(settings, store)

    result = CheckResult(CheckStatus.CRITICAL, {"age_minutes": 20})
    alerter.process("freshness", result)

    assert store.get_status("freshness") == CheckStatus.CRITICAL
    assert store.get_last_alert_ts("freshness") is not None


def test_problem_to_ok_sends_recovery() -> None:
    store = InMemoryStateStore()
    store.set_status("freshness", CheckStatus.CRITICAL)
    settings = Settings(telegram_bot_token="", telegram_chat_id="")
    alerter = Alerter(settings, store)

    alerter.process("freshness", CheckResult(CheckStatus.OK, {"age_minutes": 1}))

    assert store.get_status("freshness") == CheckStatus.OK


def test_repeated_problem_throttled() -> None:
    import time

    store = InMemoryStateStore()
    store.set_status("freshness", CheckStatus.CRITICAL)
    store.set_last_alert_ts("freshness", time.time() - 60)
    settings = Settings(telegram_bot_token="", alert_throttle_seconds=1800)
    alerter = Alerter(settings, store)
    previous_ts = store.get_last_alert_ts("freshness")

    alerter.process("freshness", CheckResult(CheckStatus.CRITICAL, {"age_minutes": 20}))

    assert store.get_last_alert_ts("freshness") == previous_ts
