"""Vendored from upstream Pillow Tests/test_image_split.py (2026-03-09).

Adapted: only test modes we support (L, RGB, RGBA).
"""
from __future__ import annotations

from PIL import Image

from .helper import assert_image_equal, hopper


def test_split() -> None:
    def split(mode):
        layers = hopper(mode).split()
        return [(i.mode, i.size[0], i.size[1]) for i in layers]

    assert split("L") == [("L", 128, 128)]
    assert split("RGB") == [("L", 128, 128), ("L", 128, 128), ("L", 128, 128)]
    assert split("RGBA") == [
        ("L", 128, 128),
        ("L", 128, 128),
        ("L", 128, 128),
        ("L", 128, 128),
    ]


def test_split_merge() -> None:
    for mode in ("L", "RGB", "RGBA"):
        expected = Image.merge(mode, hopper(mode).split())
        assert_image_equal(hopper(mode), expected)
