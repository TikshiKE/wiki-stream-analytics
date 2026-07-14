"""Placeholder test until stage 2 delivers the real consumer."""

from consumer import __version__


def test_package_importable() -> None:
    assert __version__
