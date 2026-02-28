"""
Tests adapted from upstream Pillow test_image_crop.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_crop.py
"""

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
