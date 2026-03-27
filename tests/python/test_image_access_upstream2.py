"""
Tests adapted from upstream Pillow test_image_access.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_access.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""
import pytest
from PIL import Image
from helper import hopper, assert_image_equal


def test_putpixel_getpixel_roundtrip():
    """Full put/get roundtrip — from upstream TestImagePutPixel.test_sanity."""
    im1 = hopper()
    im2 = Image.new(im1.mode, im1.size, 0)

    for y in range(im1.size[1]):
        for x in range(im1.size[0]):
            pos = x, y
            value = im1.getpixel(pos)
            im2.putpixel(pos, value)

    assert_image_equal(im1, im2)


def test_load_putpixel_roundtrip():
    """Full load() pixel access roundtrip — from upstream."""
    im1 = hopper()
    im2 = Image.new(im1.mode, im1.size, 0)

    pix1 = im1.load()
    pix2 = im2.load()

    for y in range(im1.size[1]):
        for x in range(im1.size[0]):
            pix2[x, y] = pix1[x, y]

    assert_image_equal(im1, im2)


def test_getpixel_basic_l():
    """put/getpixel roundtrip for L — from upstream TestImageGetPixel."""
    im = Image.new("L", (1, 1), 0)
    im.putpixel((0, 0), 1)
    assert im.getpixel((0, 0)) == 1


def test_getpixel_basic_rgb():
    """put/getpixel roundtrip for RGB — from upstream."""
    im = Image.new("RGB", (1, 1), 0)
    im.putpixel((0, 0), (1, 2, 3))
    assert im.getpixel((0, 0)) == (1, 2, 3)


def test_getpixel_basic_rgba():
    """put/getpixel roundtrip for RGBA — from upstream."""
    im = Image.new("RGBA", (1, 1), 0)
    im.putpixel((0, 0), (1, 2, 3, 4))
    assert im.getpixel((0, 0)) == (1, 2, 3, 4)


def test_getpixel_initial_color():
    """Image.new with initial color — from upstream."""
    im = Image.new("L", (1, 1), 42)
    assert im.getpixel((0, 0)) == 42

    im = Image.new("RGB", (1, 1), (1, 2, 3))
    assert im.getpixel((0, 0)) == (1, 2, 3)


def test_negative_index():
    """Negative indices wrap around — from upstream test_sanity_negative_index."""
    im = hopper()
    width, height = im.size
    assert im.getpixel((0, 0)) == im.getpixel((-width, -height))
    assert im.getpixel((-1, -1)) == im.getpixel((width - 1, height - 1))


def test_putpixel_negative_index():
    """putpixel with negative index — from upstream."""
    im = Image.new("L", (5, 5), 0)
    im.putpixel((-1, -1), 200)
    assert im.getpixel((4, 4)) == 200


if __name__ == "__main__":
    pytest.main()
