"""Vendored from upstream Pillow Tests/test_image_getbbox.py (2026-03-09).

Adapted: removed unsupported modes (RGBa, PA, La), removed alpha_only parameter.
"""
from __future__ import annotations

from PIL import Image

from .helper import hopper


def test_sanity() -> None:
    bbox = hopper().getbbox()
    assert isinstance(bbox, tuple)


def test_bbox() -> None:
    def check(im, fill_color):
        assert im.getbbox() is None

        im.paste(fill_color, (10, 25, 90, 75))
        assert im.getbbox() == (10, 25, 90, 75)

        im.paste(fill_color, (25, 10, 75, 90))
        assert im.getbbox() == (10, 10, 90, 90)

        im.paste(fill_color, (-10, -10, 110, 110))
        assert im.getbbox() == (0, 0, 100, 100)

    # 8-bit mode
    im = Image.new("L", (100, 100), 0)
    check(im, 255)

    # 32-bit mode
    im = Image.new("RGB", (100, 100), 0)
    check(im, 255)

    # RGBA mode
    im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    check(im, (255, 255, 255, 255))
