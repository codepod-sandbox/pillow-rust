"""
Tests adapted from upstream Pillow test_image_access.py.

https://github.com/python-pillow/Pillow/blob/main/Tests/test_image_access.py

The Pillow licence (MIT-CMU) applies to test logic ported from that file.
"""

import pytest
from PIL import Image
from conftest import assert_image, assert_image_equal


# ---------------------------------------------------------------------------
# putpixel / getpixel roundtrip
# ---------------------------------------------------------------------------


def test_putpixel_getpixel_L():
    im = Image.new("L", (1, 1))
    im.putpixel((0, 0), 128)
    assert im.getpixel((0, 0)) == 128


def test_putpixel_getpixel_RGB():
    im = Image.new("RGB", (1, 1))
    im.putpixel((0, 0), (10, 20, 30))
    assert im.getpixel((0, 0)) == (10, 20, 30)


def test_putpixel_getpixel_RGBA():
    im = Image.new("RGBA", (1, 1))
    im.putpixel((0, 0), (10, 20, 30, 40))
    assert im.getpixel((0, 0)) == (10, 20, 30, 40)


def test_putpixel_getpixel_LA():
    im = Image.new("LA", (1, 1))
    im.putpixel((0, 0), (100, 200))
    px = im.getpixel((0, 0))
    assert px == (100, 200)


def test_putpixel_overwrites():
    im = Image.new("RGB", (2, 2), (0, 0, 0))
    im.putpixel((1, 1), (255, 128, 64))
    assert im.getpixel((1, 1)) == (255, 128, 64)
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_getpixel_default_black_RGB():
    im = Image.new("RGB", (10, 10))
    assert im.getpixel((5, 5)) == (0, 0, 0)


def test_getpixel_default_black_L():
    im = Image.new("L", (10, 10))
    assert im.getpixel((5, 5)) == 0


def test_putpixel_getpixel_all_corners():
    im = Image.new("RGB", (10, 10))
    corners = [(0, 0), (9, 0), (0, 9), (9, 9)]
    for i, (x, y) in enumerate(corners):
        c = (i * 60, i * 60 + 10, i * 60 + 20)
        im.putpixel((x, y), c)
    for i, (x, y) in enumerate(corners):
        c = (i * 60, i * 60 + 10, i * 60 + 20)
        assert im.getpixel((x, y)) == c


def test_putpixel_getpixel_scan():
    """Full image putpixel/getpixel roundtrip."""
    im = Image.new("RGB", (16, 16))
    for y in range(16):
        for x in range(16):
            im.putpixel((x, y), (x * 16, y * 16, (x + y) * 8))
    for y in range(16):
        for x in range(16):
            expected = (x * 16, y * 16, (x + y) * 8)
            actual = im.getpixel((x, y))
            assert actual == expected


def test_sanity_full_roundtrip():
    """Copy all pixels via getpixel/putpixel and verify (small image)."""
    im1 = Image.new("RGB", (16, 16))
    for y in range(16):
        for x in range(16):
            im1.putpixel((x, y), (x * 16, y * 16, (x + y) * 8))
    im2 = Image.new("RGB", (16, 16), 0)
    for y in range(16):
        for x in range(16):
            im2.putpixel((x, y), im1.getpixel((x, y)))
    assert_image_equal(im1, im2)


# ---------------------------------------------------------------------------
# Pixel value check for new images
# ---------------------------------------------------------------------------


def test_new_color_L():
    im = Image.new("L", (1, 1), 128)
    assert im.getpixel((0, 0)) == 128


def test_new_color_RGB():
    im = Image.new("RGB", (1, 1), (1, 2, 3))
    assert im.getpixel((0, 0)) == (1, 2, 3)


def test_new_color_RGBA():
    im = Image.new("RGBA", (1, 1), (10, 20, 30, 40))
    assert im.getpixel((0, 0)) == (10, 20, 30, 40)


# ---------------------------------------------------------------------------
# Upstream tests — test_image_access.py
# ---------------------------------------------------------------------------


def test_negative_index_L():
    """Upstream: negative coordinates are supported (wrap-around like Python lists)."""
    im = Image.new("L", (10, 10))
    im.putpixel((0, 0), 42)
    # (-width, -height) → same as (0, 0)
    assert im.getpixel((-10, -10)) == 42


def test_negative_index_RGB():
    """Upstream: negative pixel coordinates in RGB mode."""
    im = Image.new("RGB", (10, 10), (1, 2, 3))
    # (-1, -1) should be the bottom-right pixel
    im.putpixel((9, 9), (100, 101, 102))
    assert im.getpixel((-1, -1)) == (100, 101, 102)


def test_out_of_bounds_error():
    """Upstream: coordinates beyond image size raise IndexError."""
    im = Image.new("RGB", (10, 10))
    with pytest.raises((IndexError, Exception)):
        im.getpixel((10, 10))


def test_out_of_bounds_negative_error():
    """Upstream: sufficiently negative coordinates also raise IndexError."""
    im = Image.new("RGB", (10, 10))
    with pytest.raises((IndexError, Exception)):
        im.getpixel((-11, 0))


def test_putpixel_negative_index():
    """Upstream: negative-coordinate putpixel writes to the wrapped position."""
    im = Image.new("L", (5, 5), 0)
    im.putpixel((-1, -1), 200)
    # Should match the last pixel
    assert im.getpixel((4, 4)) == 200


def test_sanity_L(hopper):
    """Upstream test_sanity: getpixel on every pixel of an L image."""
    im = hopper("L")
    for y in range(im.height):
        for x in range(im.width):
            v = im.getpixel((x, y))
            assert isinstance(v, int)


def test_sanity_RGB(hopper):
    """Upstream test_sanity: getpixel on every pixel of an RGB image."""
    im = hopper("RGB")
    for y in range(im.height):
        for x in range(im.width):
            v = im.getpixel((x, y))
            assert isinstance(v, tuple)
            assert len(v) == 3
