"""
Tests adapted from upstream Pillow test_image_crop.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_crop.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import assert_image_equal, hopper


def test_crop():
    """crop returns correct mode and size — from upstream."""
    for mode in ("L", "RGB"):
        im = hopper(mode)
        assert_image_equal(im.crop(), im)

        cropped = im.crop((50, 50, 100, 100))
        assert cropped.mode == mode
        assert cropped.size == (50, 50)


def test_wide_crop():
    """Out-of-bounds crop uses zero padding — from upstream."""
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


def test_negative_crop():
    """Reversed bbox coordinates raise ValueError — from upstream."""
    im = Image.new("RGB", (10, 10))
    for box in ((8, 2, 2, 8), (2, 8, 8, 2), (8, 8, 2, 2)):
        try:
            im.crop(box)
            raise AssertionError(f"Expected ValueError for box {box}")
        except ValueError:
            pass


def test_crop_float():
    """Float crop coordinates rounded to nearest int — from upstream.

    https://github.com/python-pillow/Pillow/issues/1744
    """
    im = Image.new("RGB", (10, 10))
    assert im.size == (10, 10)

    cropped = im.crop((0.9, 1.1, 4.2, 5.8))
    assert cropped.size == (3, 5)


def test_crop_zero():
    """Crop on zero-size image — from upstream."""
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


if __name__ == "__main__":
    pytest.main()
