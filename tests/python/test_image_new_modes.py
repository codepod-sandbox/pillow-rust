"""Tests for Image.new() — all supported modes and color formats."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Mode "L"
# ---------------------------------------------------------------------------

def test_new_L_zero():
    im = Image.new("L", (10, 10), 0)
    assert im.mode == "L"
    assert im.getpixel((0, 0)) == 0


def test_new_L_255():
    im = Image.new("L", (10, 10), 255)
    assert im.getpixel((5, 5)) == 255


def test_new_L_midrange():
    im = Image.new("L", (5, 5), 128)
    assert im.getpixel((2, 2)) == 128


def test_new_L_default_color():
    """Image.new without color defaults to 0."""
    im = Image.new("L", (5, 5))
    assert im.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# Mode "RGB"
# ---------------------------------------------------------------------------

def test_new_RGB_black():
    im = Image.new("RGB", (10, 10), (0, 0, 0))
    assert im.getpixel((0, 0)) == (0, 0, 0)


def test_new_RGB_white():
    im = Image.new("RGB", (10, 10), (255, 255, 255))
    assert im.getpixel((5, 5)) == (255, 255, 255)


def test_new_RGB_color():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    r, g, b = im.getpixel((0, 0))
    assert r == 100
    assert g == 150
    assert b == 200


def test_new_RGB_default_color():
    im = Image.new("RGB", (5, 5))
    assert im.getpixel((0, 0)) == (0, 0, 0)


# ---------------------------------------------------------------------------
# Mode "RGBA"
# ---------------------------------------------------------------------------

def test_new_RGBA_transparent():
    im = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    r, g, b, a = im.getpixel((0, 0))
    assert a == 0


def test_new_RGBA_opaque():
    im = Image.new("RGBA", (10, 10), (100, 150, 200, 255))
    r, g, b, a = im.getpixel((0, 0))
    assert r == 100
    assert g == 150
    assert b == 200
    assert a == 255


def test_new_RGBA_semi_transparent():
    im = Image.new("RGBA", (5, 5), (255, 0, 0, 128))
    r, g, b, a = im.getpixel((0, 0))
    assert r == 255
    assert a == 128


# ---------------------------------------------------------------------------
# Mode "LA"
# ---------------------------------------------------------------------------

def test_new_LA_opaque():
    im = Image.new("LA", (5, 5), (128, 255))
    l, a = im.getpixel((0, 0))
    assert l == 128
    assert a == 255


def test_new_LA_transparent():
    im = Image.new("LA", (5, 5), (200, 0))
    l, a = im.getpixel((0, 0))
    assert l == 200
    assert a == 0


# ---------------------------------------------------------------------------
# Mode "1"
# ---------------------------------------------------------------------------

def test_new_1_white():
    im = Image.new("1", (5, 5), 255)
    assert im.mode == "1"
    assert im.getpixel((0, 0)) in (255, 1, True)  # various representations


def test_new_1_black():
    im = Image.new("1", (5, 5), 0)
    assert im.mode == "1"
    assert im.getpixel((0, 0)) in (0, False)


# ---------------------------------------------------------------------------
# Size attribute
# ---------------------------------------------------------------------------

def test_new_size_attribute():
    im = Image.new("L", (20, 30), 0)
    assert im.size == (20, 30)
    assert im.width == 20
    assert im.height == 30


def test_new_size_1x1():
    im = Image.new("L", (1, 1), 128)
    assert im.size == (1, 1)


def test_new_size_large():
    im = Image.new("L", (1000, 500), 0)
    assert im.size == (1000, 500)


# ---------------------------------------------------------------------------
# All pixels have the fill color
# ---------------------------------------------------------------------------

def test_new_L_all_pixels_same():
    im = Image.new("L", (5, 5), 100)
    for y in range(5):
        for x in range(5):
            assert im.getpixel((x, y)) == 100


def test_new_RGB_all_pixels_same():
    im = Image.new("RGB", (4, 4), (10, 20, 30))
    for y in range(4):
        for x in range(4):
            assert im.getpixel((x, y)) == (10, 20, 30)


# ---------------------------------------------------------------------------
# Image.copy()
# ---------------------------------------------------------------------------

def test_copy_is_independent():
    im = Image.new("L", (5, 5), 100)
    copy = im.copy()
    copy.putpixel((0, 0), 200)
    assert im.getpixel((0, 0)) == 100  # original unchanged


def test_copy_has_same_mode():
    im = Image.new("RGB", (5, 5), (1, 2, 3))
    copy = im.copy()
    assert copy.mode == "RGB"


def test_copy_has_same_size():
    im = Image.new("L", (20, 30), 0)
    copy = im.copy()
    assert copy.size == (20, 30)


def test_copy_has_same_pixels():
    im = Image.new("L", (5, 5), 128)
    copy = im.copy()
    assert copy.getpixel((2, 2)) == 128


if __name__ == "__main__":
    pytest.main()
