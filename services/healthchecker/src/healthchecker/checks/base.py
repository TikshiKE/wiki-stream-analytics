"""Health check interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from healthchecker.models import CheckResult


class HealthCheck(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def check(self) -> CheckResult: ...
