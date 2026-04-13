"""
Tests adapted from upstream Pillow test_image_thumbnail.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_thumbnail.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper


def test_sanity():
    """thumbnail() shrinks to fit within bounding box — from upstream."""
    im = hopper()
    im.thumbnail((100, 100))
    assert im.size == (100, 100)


def test_aspect():
    """thumbnail() preserves aspect ratio — from upstream."""
    cases = [
        # (original_size, requested_size, expected_size)
        ((128, 128), (100, 100), (100, 100)),
        ((128, 64), (100, 100), (100, 50)),
        ((64, 128), (100, 100), (50, 100)),
        ((200, 100), (100, 100), (100, 50)),
        ((100, 200), (100, 100), (50, 100)),
        ((200, 200), (100, 50), (50, 50)),
        ((200, 200), (50, 100), (50, 50)),
    ]
    for original, requested, expected in cases:
        im = Image.new("L", original)
        im.thumbnail(requested)
        assert im.size == expected, (
            f"thumbnail({original}, {requested}) -> {im.size}, expected {expected}"
        )


def test_division_by_zero():
    """thumbnail() doesn't divide by zero for thin images — from upstream."""
    im = Image.new("L", (200, 2))
    im.thumbnail((75, 75))
    assert im.size == (75, 1)


def test_float():
    """thumbnail() accepts float size arguments — from upstream."""
    im = Image.new("L", (128, 128))
    im.thumbnail((99.9, 99.9))
    assert im.size == (99, 99)


if __name__ == "__main__":
    pytest.main()
