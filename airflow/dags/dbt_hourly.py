"""Hourly dbt build for analytics marts."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

from alerts import send_telegram_alert

DBT_DIR = "/opt/airflow/dbt/wiki_analytics"

default_args = {
    "owner": "wiki-stream-analytics",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": send_telegram_alert,
}

dbt_env = {
    "POSTGRES_HOST": os.environ.get("POSTGRES_HOST", "postgres"),
    "POSTGRES_PORT": os.environ.get("POSTGRES_PORT", "5432"),
    "POSTGRES_USER": os.environ.get("POSTGRES_USER", "wiki"),
    "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", "wiki"),
    "POSTGRES_DB": os.environ.get("POSTGRES_DB", "wiki"),
    "DBT_TARGET": os.environ.get("DBT_TARGET", "dev"),
    "DBT_PROFILES_DIR": DBT_DIR,
}

with DAG(
    dag_id="dbt_hourly",
    description="Run dbt build hourly to refresh staging and mart models.",
    schedule="@hourly",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    max_active_runs=1,
    tags=["dbt", "analytics"],
    default_args=default_args,
) as dag:
    BashOperator(
        task_id="dbt_build",
        bash_command=f"cd {DBT_DIR} && dbt build --profiles-dir .",
        env=dbt_env,
        append_env=True,
    )
