"""Vendored from upstream Pillow Tests/test_image_tobytes.py (2026-03-09)."""
from __future__ import annotations

from .helper import hopper


def test_sanity() -> None:
    data = hopper().tobytes()
    assert isinstance(data, bytes)
