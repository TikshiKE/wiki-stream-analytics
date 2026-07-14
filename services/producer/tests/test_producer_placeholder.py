"""Placeholder test until stage 1 delivers the real producer."""

from producer import __version__


def test_package_importable() -> None:
    assert __version__
