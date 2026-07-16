"""Hourly dbt build loop for docker-compose and Railway."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from datetime import UTC, datetime

from alerts import send_telegram_alert

DBT_DIR = os.environ.get("DBT_PROJECT_DIR", "/app/dbt/wiki_analytics")
log = logging.getLogger(__name__)


def run_dbt_build() -> int:
    env = os.environ.copy()
    env.setdefault("DBT_PROFILES_DIR", DBT_DIR)
    return subprocess.run(
        ["dbt", "build", "--profiles-dir", DBT_DIR],
        env=env,
        check=False,
    ).returncode


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    interval = int(os.environ.get("DBT_INTERVAL_SECONDS", "3600"))
    target = os.environ.get("DBT_TARGET", "dev")
    log.info("dbt-runner started target=%s interval=%ss", target, interval)

    while True:
        started = datetime.now(UTC).isoformat()
        log.info("dbt build starting at %s", started)
        code = run_dbt_build()
        if code == 0:
            log.info("dbt build succeeded")
        else:
            msg = f"dbt-runner alert: `dbt build` failed (exit {code}) at {started} UTC"
            log.error("dbt build failed exit_code=%s", code)
            send_telegram_alert(msg)
        log.info("sleeping %ss until next run", interval)
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())
