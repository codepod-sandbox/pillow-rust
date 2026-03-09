"""Vendored from upstream Pillow Tests/test_image_crop.py (2026-03-09).

Adapted: removed modes we don't support (1, P, I, F), removed external image tests.
"""
from __future__ import annotations

import pytest

from PIL import Image

from .helper import assert_image_equal, hopper


@pytest.mark.parametrize("mode", ("L", "RGB", "RGBA"))
def test_crop(mode: str) -> None:
    im = hopper(mode)
    assert_image_equal(im.crop(), im)

    cropped = im.crop((50, 50, 100, 100))
    assert cropped.mode == mode
    assert cropped.size == (50, 50)


def test_wide_crop() -> None:
    def crop(bbox):
        i = im.crop(bbox)
        h = i.histogram()
        while h and not h[-1]:
            del h[-1]
        return tuple(h)

    im = Image.new("L", (100, 100), 1)

    assert crop((0, 0, 100, 100)) == (0, 10000)
    assert crop((25, 25, 75, 75)) == (0, 2500)

    # sides
    assert crop((-25, 0, 25, 50)) == (1250, 1250)
    assert crop((0, -25, 50, 25)) == (1250, 1250)
    assert crop((75, 0, 125, 50)) == (1250, 1250)
    assert crop((0, 75, 50, 125)) == (1250, 1250)

    assert crop((-25, 25, 125, 75)) == (2500, 5000)
    assert crop((25, -25, 75, 125)) == (2500, 5000)

    # corners
    assert crop((-25, -25, 25, 25)) == (1875, 625)
    assert crop((75, -25, 125, 25)) == (1875, 625)
    assert crop((75, 75, 125, 125)) == (1875, 625)
    assert crop((-25, 75, 25, 125)) == (1875, 625)


def test_crop_zero() -> None:
    im = Image.new("RGB", (0, 0), "white")

    cropped = im.crop((0, 0, 0, 0))
    assert cropped.size == (0, 0)

    cropped = im.crop((10, 10, 20, 20))
    assert cropped.size == (10, 10)
    assert cropped.getpixel((0, 0)) == (0, 0, 0)

    im = Image.new("RGB", (0, 0))

    cropped = im.crop((10, 10, 20, 20))
    assert cropped.size == (10, 10)
    assert cropped.getpixel((2, 0)) == (0, 0, 0)
