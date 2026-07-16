"""Telegram alerting with state transitions and throttling."""

from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request

import structlog

from healthchecker.config import Settings
from healthchecker.models import CheckResult, CheckStatus
from healthchecker.state_store import StateStore, should_send_alert

log = structlog.get_logger(__name__)


class Alerter:
    def __init__(self, settings: Settings, store: StateStore) -> None:
        self._settings = settings
        self._store = store

    def process(self, check_name: str, result: CheckResult) -> None:
        previous = self._store.get_status(check_name)
        current = result.status
        now = time.time()

        if previous is None:
            self._store.set_status(check_name, current)
            if current.is_problem:
                self._maybe_send_problem(check_name, result, now)
            return

        if previous == current:
            if current.is_problem:
                self._maybe_send_problem(check_name, result, now)
            return

        if not previous.is_problem and current.is_problem:
            self._store.set_status(check_name, current)
            self._maybe_send_problem(check_name, result, now)
            return

        if previous.is_problem and current == CheckStatus.OK:
            self._store.set_status(check_name, current)
            self._send(
                check_name,
                f"✅ RECOVERED `{check_name}` is OK again\n{self._format_details(result)}",
                now,
            )
            return

        self._store.set_status(check_name, current)
        if current.is_problem:
            self._maybe_send_problem(check_name, result, now)

    def _maybe_send_problem(self, check_name: str, result: CheckResult, now: float) -> None:
        last_alert = self._store.get_last_alert_ts(check_name)
        if not should_send_alert(last_alert, now, self._settings.alert_throttle_seconds):
            log.info(
                "alert_throttled",
                check=check_name,
                status=result.status.value,
            )
            return
        emoji = "🔴" if result.status == CheckStatus.CRITICAL else "🟠"
        self._send(
            check_name,
            f"{emoji} PROBLEM `{check_name}` → {result.status.value.upper()}\n"
            f"{self._format_details(result)}",
            now,
        )

    def _send(self, check_name: str, message: str, now: float) -> None:
        token = self._settings.telegram_bot_token.strip()
        chat_id = self._settings.telegram_chat_id.strip()
        if not token or not chat_id:
            log.warning("telegram_not_configured", check=check_name, message=message)
            self._store.set_last_alert_ts(check_name, now)
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = urllib.parse.urlencode(
            {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        ).encode()
        req = urllib.request.Request(url, data=payload, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    log.error("telegram_send_failed", check=check_name, status=resp.status)
                    return
        except urllib.error.URLError as exc:
            log.error("telegram_send_error", check=check_name, error=str(exc))
            return

        self._store.set_last_alert_ts(check_name, now)
        log.info("telegram_alert_sent", check=check_name)

    @staticmethod
    def _format_details(result: CheckResult) -> str:
        if not result.details:
            return ""
        parts = [f"• {key}: {value}" for key, value in result.details.items()]
        return "\n".join(parts[:8])
