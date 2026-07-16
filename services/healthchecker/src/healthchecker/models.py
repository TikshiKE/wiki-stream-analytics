"""Health check result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class CheckStatus(StrEnum):
    OK = "ok"
    WARN = "warn"
    CRITICAL = "critical"

    @property
    def is_problem(self) -> bool:
        return self in {CheckStatus.WARN, CheckStatus.CRITICAL}


@dataclass(frozen=True)
class CheckResult:
    status: CheckStatus
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedHealth:
    status: CheckStatus
    checks: dict[str, CheckResult]
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "checked_at": self.checked_at.isoformat(),
            "checks": {
                name: {"status": result.status.value, "details": result.details}
                for name, result in self.checks.items()
            },
        }

    @staticmethod
    def aggregate(checks: dict[str, CheckResult]) -> CheckStatus:
        if any(r.status == CheckStatus.CRITICAL for r in checks.values()):
            return CheckStatus.CRITICAL
        if any(r.status == CheckStatus.WARN for r in checks.values()):
            return CheckStatus.WARN
        return CheckStatus.OK
