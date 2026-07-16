"""Tests for Wikipedia URL helpers."""

from dashboard.urls import page_url


def test_enwiki_page_url() -> None:
    url = page_url("enwiki", "Earth")
    assert url == "https://en.wikipedia.org/wiki/Earth"


def test_ruwiki_page_url_spaces() -> None:
    url = page_url("ruwiki", "Земля")
    assert url.startswith("https://ru.wikipedia.org/wiki/")


def test_wiktionary_url() -> None:
    url = page_url("enwiktionary", "hello")
    assert url == "https://en.wiktionary.org/wiki/hello"
