"""Airflow DAG import tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

AIRFLOW_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AIRFLOW_ROOT.parent


@pytest.fixture()
def airflow_env(tmp_path, monkeypatch):
    airflow_home = tmp_path / "airflow_home"
    airflow_home.mkdir()
    db_path = airflow_home / "airflow.db"
    monkeypatch.setenv("AIRFLOW_HOME", str(airflow_home))
    monkeypatch.setenv("AIRFLOW__CORE__UNIT_TEST_MODE", "True")
    monkeypatch.setenv("AIRFLOW__CORE__LOAD_EXAMPLES", "False")
    monkeypatch.setenv("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("POSTGRES_HOST", "postgres")
    monkeypatch.setenv("POSTGRES_USER", "wiki")
    monkeypatch.setenv("POSTGRES_PASSWORD", "wiki")
    monkeypatch.setenv("POSTGRES_DB", "wiki")
    sys.path.insert(0, str(AIRFLOW_ROOT))
    sys.path.insert(0, str(AIRFLOW_ROOT / "plugins"))
    yield
    skip = {str(AIRFLOW_ROOT), str(AIRFLOW_ROOT / "plugins")}
    sys.path[:] = [p for p in sys.path if p not in skip]


def test_dagbag_has_no_import_errors(airflow_env):
    pytest.importorskip("airflow")
    from airflow.models import DagBag

    dag_folder = str(AIRFLOW_ROOT / "dags")
    bag = DagBag(dag_folder=dag_folder, include_examples=False)
    assert bag.import_errors == {}, f"DAG import errors: {bag.import_errors}"
    assert "maintenance_daily" in bag.dags
