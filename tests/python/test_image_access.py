"""Tests for pixel access: getpixel, putpixel, load(), edge cases."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# getpixel() — basic
# ---------------------------------------------------------------------------

def test_getpixel_L():
    im = Image.new("L", (5, 5), 128)
    assert im.getpixel((2, 2)) == 128


def test_getpixel_RGB():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    px = im.getpixel((0, 0))
    assert px == (10, 20, 30)


def test_getpixel_RGBA():
    im = Image.new("RGBA", (5, 5), (10, 20, 30, 200))
    px = im.getpixel((0, 0))
    assert px == (10, 20, 30, 200)


def test_getpixel_LA():
    im = Image.new("LA", (5, 5), (128, 200))
    px = im.getpixel((0, 0))
    assert px == (128, 200)


def test_getpixel_1_mode():
    im = Image.new("1", (5, 5), 0)
    im.putpixel((2, 2), 255)
    assert im.getpixel((2, 2)) != 0
    assert im.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# putpixel() — basic
# ---------------------------------------------------------------------------

def test_putpixel_L_scalar():
    im = Image.new("L", (5, 5), 0)
    im.putpixel((2, 2), 200)
    assert im.getpixel((2, 2)) == 200
    assert im.getpixel((0, 0)) == 0


def test_putpixel_RGB_tuple():
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    im.putpixel((1, 1), (255, 128, 64))
    assert im.getpixel((1, 1)) == (255, 128, 64)
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_putpixel_RGBA_tuple():
    im = Image.new("RGBA", (5, 5), (0, 0, 0, 255))
    im.putpixel((3, 3), (100, 200, 50, 128))
    assert im.getpixel((3, 3)) == (100, 200, 50, 128)


def test_putpixel_overwrites_previous():
    im = Image.new("L", (5, 5), 0)
    im.putpixel((2, 2), 100)
    im.putpixel((2, 2), 200)
    assert im.getpixel((2, 2)) == 200


def test_putpixel_LA_tuple():
    im = Image.new("LA", (5, 5), (0, 255))
    im.putpixel((0, 0), (128, 200))
    px = im.getpixel((0, 0))
    assert px == (128, 200)


# ---------------------------------------------------------------------------
# Boundary pixels
# ---------------------------------------------------------------------------

def test_getpixel_corners():
    im = Image.new("L", (10, 8), 0)
    corners = [(0, 0), (9, 0), (0, 7), (9, 7)]
    for i, c in enumerate(corners):
        im.putpixel(c, (i + 1) * 50)
    for i, c in enumerate(corners):
        assert im.getpixel(c) == (i + 1) * 50


def test_putpixel_first_and_last():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((0, 0), (255, 0, 0))
    im.putpixel((9, 9), (0, 0, 255))
    assert im.getpixel((0, 0)) == (255, 0, 0)
    assert im.getpixel((9, 9)) == (0, 0, 255)


# ---------------------------------------------------------------------------
# load() pixel access
# ---------------------------------------------------------------------------

def test_load_getitem_L():
    im = Image.new("L", (5, 5), 128)
    px = im.load()
    assert px[2, 2] == 128


def test_load_getitem_RGB():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    px = im.load()
    assert px[0, 0] == (10, 20, 30)


def test_load_setitem_L():
    im = Image.new("L", (5, 5), 0)
    px = im.load()
    px[2, 2] = 200
    assert im.getpixel((2, 2)) == 200


def test_load_setitem_RGB():
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    px = im.load()
    px[1, 1] = (100, 150, 200)
    assert im.getpixel((1, 1)) == (100, 150, 200)


# ---------------------------------------------------------------------------
# putdata() and getdata()
# ---------------------------------------------------------------------------

def test_putdata_getdata_roundtrip_L():
    im = Image.new("L", (3, 2), 0)
    data = [10, 20, 30, 40, 50, 60]
    im.putdata(data)
    out = list(im.getdata())
    assert out == data


def test_putdata_getdata_roundtrip_RGB():
    im = Image.new("RGB", (2, 2), 0)
    data = [(10, 20, 30), (40, 50, 60), (70, 80, 90), (100, 110, 120)]
    im.putdata(data)
    out = list(im.getdata())
    assert out == data


def test_getdata_len():
    im = Image.new("L", (10, 8), 0)
    assert len(im.getdata()) == 80


def test_putdata_partial():
    """putdata starting at offset."""
    im = Image.new("L", (5, 1), 0)
    # Should fill from the beginning
    im.putdata([100, 200, 150, 50, 75])
    assert im.getpixel((0, 0)) == 100
    assert im.getpixel((4, 0)) == 75


# ---------------------------------------------------------------------------
# Pixel value clamping
# ---------------------------------------------------------------------------

def test_getpixel_L_range():
    """All values in L image should be 0-255."""
    im = Image.new("L", (256, 1), 0)
    for i in range(256):
        im.putpixel((i, 0), i)
    for i in range(256):
        val = im.getpixel((i, 0))
        assert 0 <= int(val) <= 255


if __name__ == "__main__":
    pytest.main()
