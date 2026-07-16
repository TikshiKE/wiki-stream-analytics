"""Map Wikimedia recentchange JSON payloads to Postgres rows."""

from __future__ import annotations

import ipaddress
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

WRITABLE_TYPES = frozenset({"edit", "new"})


@dataclass(frozen=True, slots=True)
class RecentChangeRow:
    event_id: UUID
    event_ts: datetime
    wiki: str
    domain: str
    change_type: str
    namespace: int | None
    title: str | None
    user_name: str | None
    is_bot: bool
    is_anonymous: bool
    is_minor: bool
    comment: str | None
    length_old: int | None
    length_new: int | None


def is_anonymous_user(user: str | None) -> bool:
    if not user:
        return False
    try:
        ipaddress.ip_address(user)
    except ValueError:
        return False
    return True


def should_persist(change_type: str) -> bool:
    return change_type in WRITABLE_TYPES


def parse_payload(raw: str) -> dict[str, Any]:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("not_an_object")
    return payload


def row_from_payload(payload: dict[str, Any]) -> RecentChangeRow:
    meta = payload.get("meta") or {}
    if not meta.get("id"):
        raise ValueError("missing_meta_id")
    length = payload.get("length") or {}
    user = payload.get("user")
    return RecentChangeRow(
        event_id=UUID(meta["id"]),
        event_ts=datetime.fromisoformat(meta["dt"].replace("Z", "+00:00")),
        wiki=payload["wiki"],
        domain=meta.get("domain") or "",
        change_type=payload["type"],
        namespace=payload.get("namespace"),
        title=payload.get("title"),
        user_name=user,
        is_bot=bool(payload.get("bot")),
        is_anonymous=is_anonymous_user(user),
        is_minor=bool(payload.get("minor")),
        comment=payload.get("comment"),
        length_old=length.get("old"),
        length_new=length.get("new"),
    )


def row_to_tuple(row: RecentChangeRow) -> tuple:
    return (
        row.event_id,
        row.event_ts,
        row.wiki,
        row.domain,
        row.change_type,
        row.namespace,
        row.title,
        row.user_name,
        row.is_bot,
        row.is_anonymous,
        row.is_minor,
        row.comment,
        row.length_old,
        row.length_new,
    )
