"""Telegram alerts for dbt-runner failures."""

from __future__ import annotations

import logging
import os
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)


def send_telegram_alert(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        log.warning("telegram_not_configured message=%s", message)
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    ).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                log.error("telegram_send_failed status=%s", resp.status)
    except urllib.error.URLError as exc:
        log.error("telegram_send_error error=%s", exc)
