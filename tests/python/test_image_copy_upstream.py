"""
Tests adapted from upstream Pillow test_image_copy.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_copy.py
"""

from PIL import Image
from conftest import assert_image, assert_image_equal


def test_copy_L(hopper):
    im = hopper("L")
    out = im.copy()
    assert out.mode == im.mode
    assert out.size == im.size


def test_copy_RGB(hopper):
    im = hopper("RGB")
    out = im.copy()
    assert out.mode == im.mode
    assert out.size == im.size


def test_copy_RGBA(hopper):
    im = hopper("RGBA")
    out = im.copy()
    assert out.mode == im.mode
    assert out.size == im.size


def test_copy_cropped_L(hopper):
    im = hopper("L")
    out = im.crop((10, 10, 20, 20)).copy()
    assert out.mode == im.mode
    assert out.size == (10, 10)


def test_copy_cropped_RGB(hopper):
    im = hopper("RGB")
    out = im.crop((10, 10, 20, 20)).copy()
    assert out.mode == im.mode
    assert out.size == (10, 10)


def test_copy_equal(hopper):
    im = hopper("RGB")
    out = im.copy()
    assert_image_equal(im, out)


def test_copy_independence():
    """Modifying the copy must not affect the original."""
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    out = im.copy()
    out.putpixel((0, 0), (99, 99, 99))
    assert im.getpixel((0, 0)) == (1, 2, 3)
    assert out.getpixel((0, 0)) == (99, 99, 99)
