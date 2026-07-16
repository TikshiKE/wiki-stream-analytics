"""Shared sample payloads for consumer tests."""

SAMPLE_EDIT = """
{
  "meta": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "dt": "2026-07-14T12:00:00Z",
    "domain": "en.wikipedia.org"
  },
  "type": "edit",
  "wiki": "enwiki",
  "namespace": 0,
  "title": "Earth",
  "user": "127.0.0.1",
  "bot": false,
  "minor": false,
  "comment": "fix typo",
  "length": {"old": 100, "new": 105}
}
"""

SAMPLE_MINIMAL = """
{
  "meta": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "dt": "2026-07-14T12:00:00Z",
    "domain": "en.wikipedia.org"
  },
  "type": "edit",
  "wiki": "enwiki",
  "user": "Alice"
}
"""
