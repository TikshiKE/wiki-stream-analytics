"""Daily maintenance: partitions, retention, vacuum, and data quality checks."""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from airflow.operators.python import PythonOperator

from airflow import DAG

# lib/ lives one level above dags/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alerts import send_telegram_alert
from lib.maintenance import (
    check_freshness,
    check_volume,
    create_raw_partitions,
    drop_old_partitions,
    vacuum_marts,
)

default_args = {
    "owner": "wiki-stream-analytics",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": send_telegram_alert,
}


def _create_partitions() -> None:
    create_raw_partitions(days_ahead=3)


def _drop_partitions() -> None:
    retention = int(os.environ.get("RETENTION_DAYS", "7"))
    drop_old_partitions(retention_days=retention)


with DAG(
    dag_id="maintenance_daily",
    description=(
        "Daily raw partition management, mart vacuum, and DQ checks "
        "(freshness + volume anomaly detection)."
    ),
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    max_active_runs=1,
    tags=["maintenance", "dq"],
    default_args=default_args,
) as dag:
    create_partitions = PythonOperator(
        task_id="create_partitions",
        python_callable=_create_partitions,
    )
    drop_partitions = PythonOperator(
        task_id="drop_old_partitions",
        python_callable=_drop_partitions,
    )
    vacuum = PythonOperator(
        task_id="vacuum_marts",
        python_callable=vacuum_marts,
    )
    dq_freshness = PythonOperator(
        task_id="dq_freshness",
        python_callable=lambda: check_freshness(max_age_minutes=10),
    )
    dq_volume = PythonOperator(
        task_id="dq_volume",
        python_callable=lambda: check_volume(tolerance=0.6),
    )

    create_partitions >> drop_partitions >> vacuum >> [dq_freshness, dq_volume]
