"""Placeholder test until stage 6 delivers the real healthchecker."""

from healthchecker import __version__


def test_package_importable() -> None:
    assert __version__
