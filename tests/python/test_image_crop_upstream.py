"""
Tests adapted from upstream Pillow test_image_crop.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_crop.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
from PIL import Image
from conftest import assert_image, assert_image_equal


def test_crop_L(hopper):
    im = hopper("L")
    assert_image_equal(im.crop(), im)
    cropped = im.crop((50, 50, 100, 100))
    assert cropped.mode == "L"
    assert cropped.size == (50, 50)


def test_crop_RGB(hopper):
    im = hopper("RGB")
    assert_image_equal(im.crop(), im)
    cropped = im.crop((50, 50, 100, 100))
    assert cropped.mode == "RGB"
    assert cropped.size == (50, 50)


def test_crop_RGBA(hopper):
    im = hopper("RGBA")
    cropped = im.crop((50, 50, 100, 100))
    assert cropped.mode == "RGBA"
    assert cropped.size == (50, 50)


def test_crop_preserves_pixels():
    im = Image.new("RGB", (100, 100), (42, 43, 44))
    cropped = im.crop((25, 25, 75, 75))
    assert cropped.getpixel((0, 0)) == (42, 43, 44)
    assert cropped.getpixel((24, 24)) == (42, 43, 44)


def test_crop_none(hopper):
    """crop() with no args should return a full copy."""
    im = hopper("RGB")
    cropped = im.crop()
    assert_image_equal(cropped, im)


def test_crop_full():
    im = Image.new("RGB", (100, 100), (1, 2, 3))
    cropped = im.crop((0, 0, 100, 100))
    assert_image(cropped, "RGB", (100, 100))
    assert cropped.getpixel((0, 0)) == (1, 2, 3)


def test_crop_single_pixel():
    im = Image.new("RGB", (10, 10), (5, 6, 7))
    im.putpixel((3, 4), (99, 98, 97))
    cropped = im.crop((3, 4, 4, 5))
    assert_image(cropped, "RGB", (1, 1))
    assert cropped.getpixel((0, 0)) == (99, 98, 97)


def test_crop_preserves_mode(hopper):
    for mode in ("L", "RGB", "RGBA"):
        im = hopper(mode)
        out = im.crop((10, 10, 50, 50))
        assert out.mode == mode


# ---------------------------------------------------------------------------
# Upstream tests — test_image_crop.py
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("box", ((8, 2, 2, 8), (2, 8, 8, 2), (8, 8, 2, 2)))
def test_negative_crop(box):
    """Upstream: crop raises ValueError when right < left or bottom < top."""
    im = Image.new("RGB", (10, 10))
    with pytest.raises(ValueError):
        im.crop(box)


def test_crop_float():
    """Upstream: float crop coordinates are rounded to nearest integer.

    Adapted from test_image_crop.py in Pillow (issue #1744).
    """
    im = Image.new("RGB", (10, 10))
    assert im.size == (10, 10)
    cropped = im.crop((0.9, 1.1, 4.2, 5.8))
    assert cropped.size == (3, 5)


def test_crop_zero():
    """Upstream: cropping a zero-size image should return correct sizes.

    Adapted from test_image_crop.py in Pillow.
    """
    im = Image.new("RGB", (0, 0), "white")

    cropped = im.crop((0, 0, 0, 0))
    assert cropped.size == (0, 0)

    cropped = im.crop((10, 10, 20, 20))
    assert cropped.size == (10, 10)
    assert cropped.getpixel((0, 0)) == (0, 0, 0)


def test_wide_crop():
    """Upstream: crop with coordinates extending outside the image.

    Adapted from test_image_crop.py in Pillow.
    Outside-image pixels should read as zero (black).
    """
    im = Image.new("L", (100, 100), 1)

    # Full image
    c = im.crop((0, 0, 100, 100))
    assert c.size == (100, 100)
    assert c.getpixel((0, 0)) == 1

    # Crop fully inside
    c = im.crop((25, 25, 75, 75))
    assert c.size == (50, 50)
    assert c.getpixel((0, 0)) == 1

    # Crop extending left of image — left half should be black
    c = im.crop((-10, 0, 10, 10))
    assert c.size == (20, 10)
    assert c.getpixel((0, 0)) == 0      # outside → black
    assert c.getpixel((10, 0)) == 1     # inside → 1

    # Crop fully outside should give zeros
    c = im.crop((200, 0, 210, 10))
    assert c.size == (10, 10)
    assert c.getpixel((0, 0)) == 0
