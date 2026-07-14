"""Pydantic models and parsing for Wikimedia recentchange events."""

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, ValidationError


class ParseError(Exception):
    """Raised when an incoming SSE payload cannot be turned into a valid event."""

    def __init__(self, reason: str, raw: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.raw = raw


class EventMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    dt: datetime
    domain: str = ""


class PageLength(BaseModel):
    model_config = ConfigDict(extra="ignore")

    old: int | None = None
    new: int | None = None


class RecentChangeEvent(BaseModel):
    """Validated recentchange event; extra fields are ignored, raw JSON travels to Kafka."""

    model_config = ConfigDict(extra="ignore")

    meta: EventMeta
    type: str
    wiki: str
    namespace: int | None = None
    title: str | None = None
    user: str | None = None
    bot: bool = False
    minor: bool = False
    comment: str | None = None
    length: PageLength | None = None
    server_name: str | None = None


def parse_event(raw: str) -> RecentChangeEvent:
    """Parse a raw SSE data payload into a validated event.

    Raises ParseError with a machine-readable reason (used as a DLQ header).
    """
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ParseError("invalid_json", raw) from exc
    if not isinstance(payload, dict):
        raise ParseError("not_an_object", raw)
    try:
        return RecentChangeEvent.model_validate(payload)
    except ValidationError as exc:
        raise ParseError("schema_validation_failed", raw) from exc
