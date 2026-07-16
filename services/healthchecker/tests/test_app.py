"""Tests for /health HTTP endpoint."""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from healthchecker.app import create_app
from healthchecker.models import AggregatedHealth, CheckResult, CheckStatus
from healthchecker.runner import CheckRunner


def test_health_endpoint_ok() -> None:
    runner = MagicMock(spec=CheckRunner)
    runner.latest = AggregatedHealth(
        status=CheckStatus.OK,
        checks={
            "freshness": CheckResult(CheckStatus.OK, {"age_minutes": 1}),
            "redis": CheckResult(CheckStatus.OK, {"live_minutes_with_data": 3}),
        },
    )
    client = TestClient(create_app(runner))
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "freshness" in body["checks"]
    assert body["checks"]["freshness"]["status"] == "ok"


def test_health_endpoint_critical_returns_503() -> None:
    runner = MagicMock(spec=CheckRunner)
    runner.latest = AggregatedHealth(
        status=CheckStatus.CRITICAL,
        checks={"freshness": CheckResult(CheckStatus.CRITICAL, {"age_minutes": 20})},
    )
    client = TestClient(create_app(runner))
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "critical"
