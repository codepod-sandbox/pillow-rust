"""Tests for Image.putpixel() and getpixel() — exact round-trip values."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# L mode round-trips
# ---------------------------------------------------------------------------

def test_putpixel_getpixel_L_zero():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 0)
    assert im.getpixel((5, 5)) == 0


def test_putpixel_getpixel_L_255():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 255)
    assert im.getpixel((5, 5)) == 255


def test_putpixel_getpixel_L_midrange():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((3, 7), 128)
    assert im.getpixel((3, 7)) == 128


def test_putpixel_L_all_values():
    """Test all 256 values round-trip correctly."""
    im = Image.new("L", (16, 16), 0)
    for v in range(256):
        x, y = v % 16, v // 16
        im.putpixel((x, y), v)
    for v in range(256):
        x, y = v % 16, v // 16
        assert im.getpixel((x, y)) == v, f"Failed at value {v}"


# ---------------------------------------------------------------------------
# RGB mode round-trips
# ---------------------------------------------------------------------------

def test_putpixel_getpixel_RGB_black():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((3, 3), (0, 0, 0))
    assert im.getpixel((3, 3)) == (0, 0, 0)


def test_putpixel_getpixel_RGB_white():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((3, 3), (255, 255, 255))
    assert im.getpixel((3, 3)) == (255, 255, 255)


def test_putpixel_getpixel_RGB_color():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((4, 6), (100, 150, 200))
    r, g, b = im.getpixel((4, 6))
    assert r == 100
    assert g == 150
    assert b == 200


def test_putpixel_getpixel_RGB_independent_channels():
    """Each channel stored independently."""
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    im.putpixel((0, 0), (255, 0, 0))
    im.putpixel((1, 0), (0, 255, 0))
    im.putpixel((2, 0), (0, 0, 255))
    assert im.getpixel((0, 0)) == (255, 0, 0)
    assert im.getpixel((1, 0)) == (0, 255, 0)
    assert im.getpixel((2, 0)) == (0, 0, 255)


# ---------------------------------------------------------------------------
# RGBA mode round-trips
# ---------------------------------------------------------------------------

def test_putpixel_getpixel_RGBA():
    im = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    im.putpixel((3, 3), (100, 150, 200, 128))
    r, g, b, a = im.getpixel((3, 3))
    assert r == 100
    assert g == 150
    assert b == 200
    assert a == 128


def test_putpixel_RGBA_alpha_zero():
    im = Image.new("RGBA", (5, 5), (255, 255, 255, 255))
    im.putpixel((0, 0), (100, 100, 100, 0))
    r, g, b, a = im.getpixel((0, 0))
    assert a == 0


def test_putpixel_RGBA_alpha_255():
    im = Image.new("RGBA", (5, 5), (0, 0, 0, 0))
    im.putpixel((0, 0), (100, 100, 100, 255))
    r, g, b, a = im.getpixel((0, 0))
    assert a == 255


# ---------------------------------------------------------------------------
# Overwrite behavior
# ---------------------------------------------------------------------------

def test_putpixel_overwrites():
    im = Image.new("L", (10, 10), 100)
    im.putpixel((5, 5), 200)
    assert im.getpixel((5, 5)) == 200
    im.putpixel((5, 5), 50)
    assert im.getpixel((5, 5)) == 50


def test_putpixel_does_not_affect_neighbors():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((5, 5), 200)
    assert im.getpixel((4, 5)) == 0
    assert im.getpixel((6, 5)) == 0
    assert im.getpixel((5, 4)) == 0
    assert im.getpixel((5, 6)) == 0


# ---------------------------------------------------------------------------
# Edge pixels
# ---------------------------------------------------------------------------

def test_putpixel_top_left():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 100)
    assert im.getpixel((0, 0)) == 100


def test_putpixel_top_right():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((9, 0), 100)
    assert im.getpixel((9, 0)) == 100


def test_putpixel_bottom_left():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 9), 100)
    assert im.getpixel((0, 9)) == 100


def test_putpixel_bottom_right():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((9, 9), 100)
    assert im.getpixel((9, 9)) == 100


# ---------------------------------------------------------------------------
# LA mode
# ---------------------------------------------------------------------------

def test_putpixel_getpixel_LA():
    im = Image.new("LA", (5, 5), (0, 0))
    im.putpixel((2, 2), (128, 200))
    l, a = im.getpixel((2, 2))
    assert l == 128
    assert a == 200


if __name__ == "__main__":
    pytest.main()
