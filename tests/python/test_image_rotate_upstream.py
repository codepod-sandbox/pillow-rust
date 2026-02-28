"""
Tests adapted from upstream Pillow test_image_rotate.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_rotate.py
"""

from PIL import Image
from conftest import assert_image, assert_image_equal


def test_rotate_L(hopper):
    im = hopper("L")
    out = im.rotate(45)
    assert out.mode == "L"
    assert out.size == im.size


def test_rotate_RGB(hopper):
    im = hopper("RGB")
    out = im.rotate(45)
    assert out.mode == "RGB"
    assert out.size == im.size


def test_rotate_RGBA(hopper):
    im = hopper("RGBA")
    out = im.rotate(45)
    assert out.mode == "RGBA"


def test_rotate_0(hopper):
    im = hopper("RGB")
    out = im.rotate(0)
    assert_image(out, "RGB", im.size)


def test_rotate_90_size():
    im = Image.new("RGB", (100, 50))
    out = im.rotate(90)
    assert out.size == (50, 100)


def test_rotate_180_size():
    im = Image.new("RGB", (100, 50))
    out = im.rotate(180)
    assert out.size == (100, 50)


def test_rotate_270_size():
    im = Image.new("RGB", (100, 50))
    out = im.rotate(270)
    assert out.size == (50, 100)


def test_rotate_360(hopper):
    im = hopper("RGB")
    out = im.rotate(360)
    assert_image(out, "RGB", im.size)


def test_rotate_90_pixel():
    im = Image.new("RGB", (10, 20))
    im.putpixel((0, 0), (255, 0, 0))
    out = im.rotate(90)
    assert out.size == (20, 10)
    assert out.getpixel((0, 9)) == (255, 0, 0)


def test_rotate_180_pixel():
    im = Image.new("RGB", (10, 10))
    im.putpixel((0, 0), (255, 0, 0))
    out = im.rotate(180)
    assert out.getpixel((9, 9)) == (255, 0, 0)


def test_rotate_270_pixel():
    im = Image.new("RGB", (10, 20))
    im.putpixel((0, 0), (255, 0, 0))
    out = im.rotate(270)
    assert out.size == (20, 10)
    assert out.getpixel((19, 0)) == (255, 0, 0)


def test_rotate_arbitrary():
    """Non-90deg rotation should keep same dimensions, no crash."""
    im = Image.new("RGB", (100, 100), (0, 255, 0))
    out = im.rotate(45)
    assert_image(out, im.mode, im.size)


def test_rotate_90_mode_preservation(hopper):
    for mode in ("L", "RGB", "RGBA"):
        im = hopper(mode)
        out = im.rotate(90)
        assert out.mode == mode
