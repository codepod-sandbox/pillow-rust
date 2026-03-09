"""Vendored from upstream Pillow Tests/test_image_copy.py (2026-03-09).

Adapted: removed modes we don't support (1, P, I, F), removed libtiff test.
"""
from __future__ import annotations

import copy

import pytest

from PIL import Image

from .helper import assert_image_equal, hopper


@pytest.mark.parametrize("mode", ("L", "RGB", "RGBA"))
def test_copy(mode: str) -> None:
    im = hopper(mode)
    out = im.copy()
    assert out.mode == mode
    assert out.size == im.size

    # also test copy module
    out2 = copy.copy(im)
    assert out2.mode == mode
    assert out2.size == im.size

    # cropped copy
    cropped = im.crop((10, 10, 20, 20))
    out3 = cropped.copy()
    assert out3.mode == mode
    assert out3.size == (10, 10)


def test_copy_zero() -> None:
    im = Image.new("RGB", (0, 0))
    out = im.copy()
    assert out.mode == "RGB"
    assert out.size == (0, 0)
