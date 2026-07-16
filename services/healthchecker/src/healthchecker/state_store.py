"""Redis-backed check state and alert throttling."""

from __future__ import annotations

from typing import Protocol

from healthchecker.models import CheckStatus


class StateStore(Protocol):
    def get_status(self, check_name: str) -> CheckStatus | None: ...

    def set_status(self, check_name: str, status: CheckStatus) -> None: ...

    def get_last_alert_ts(self, check_name: str) -> float | None: ...

    def set_last_alert_ts(self, check_name: str, ts: float) -> None: ...


class RedisStateStore:
    def __init__(self, client, prefix: str = "healthchecker") -> None:
        self._client = client
        self._prefix = prefix

    def _status_key(self, check_name: str) -> str:
        return f"{self._prefix}:state:{check_name}"

    def _alert_key(self, check_name: str) -> str:
        return f"{self._prefix}:last_alert:{check_name}"

    def get_status(self, check_name: str) -> CheckStatus | None:
        value = self._client.get(self._status_key(check_name))
        if value is None:
            return None
        return CheckStatus(value)

    def set_status(self, check_name: str, status: CheckStatus) -> None:
        self._client.set(self._status_key(check_name), status.value)

    def get_last_alert_ts(self, check_name: str) -> float | None:
        value = self._client.get(self._alert_key(check_name))
        return float(value) if value is not None else None

    def set_last_alert_ts(self, check_name: str, ts: float) -> None:
        self._client.set(self._alert_key(check_name), str(ts))


class InMemoryStateStore:
    """Used in unit tests."""

    def __init__(self) -> None:
        self.statuses: dict[str, CheckStatus] = {}
        self.last_alerts: dict[str, float] = {}

    def get_status(self, check_name: str) -> CheckStatus | None:
        return self.statuses.get(check_name)

    def set_status(self, check_name: str, status: CheckStatus) -> None:
        self.statuses[check_name] = status

    def get_last_alert_ts(self, check_name: str) -> float | None:
        return self.last_alerts.get(check_name)

    def set_last_alert_ts(self, check_name: str, ts: float) -> None:
        self.last_alerts[check_name] = ts


def should_send_alert(
    last_alert_ts: float | None,
    now: float,
    throttle_seconds: int,
) -> bool:
    if last_alert_ts is None:
        return True
    return (now - last_alert_ts) >= throttle_seconds
