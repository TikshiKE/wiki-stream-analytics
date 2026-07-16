"""Telegram alert callbacks for Airflow DAG failures."""

from __future__ import annotations

import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

log = logging.getLogger(__name__)


def send_telegram_alert(context: dict[str, Any]) -> None:
    """Airflow on_failure_callback: notify Telegram or log if not configured."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    dag = context.get("dag")
    ti = context.get("task_instance")
    dag_id = dag.dag_id if dag else "unknown"
    task_id = ti.task_id if ti else "unknown"
    message = f"Airflow alert: DAG `{dag_id}` task `{task_id}` failed"

    if not token or not chat_id:
        log.warning("telegram_not_configured dag=%s task=%s", dag_id, task_id)
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
