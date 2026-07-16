"""Wikipedia article URL helpers."""

from __future__ import annotations

from urllib.parse import quote

_PROJECT_SUFFIXES: tuple[tuple[str, str], ...] = (
    ("wiktionary", "wiktionary.org"),
    ("wikibooks", "wikibooks.org"),
    ("wikinews", "wikinews.org"),
    ("wikiquote", "wikiquote.org"),
    ("wikisource", "wikisource.org"),
    ("wikivoyage", "wikivoyage.org"),
    ("wiki", "wikipedia.org"),
)


def page_url(wiki: str, title: str) -> str:
    """Build a MediaWiki article URL from wiki code and page title."""
    path = quote(title.replace(" ", "_"), safe="/:")
    for suffix, domain in _PROJECT_SUFFIXES:
        if wiki.endswith(suffix):
            lang = wiki[: -len(suffix)]
            host = f"{lang}.{domain}" if lang else f"www.{domain}"
            return f"https://{host}/wiki/{path}"
    return f"https://www.wikipedia.org/wiki/{path}"
