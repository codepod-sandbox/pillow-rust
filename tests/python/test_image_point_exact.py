"""Tests for Image.point() — lookup table and function mapping."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# point() with a function
# ---------------------------------------------------------------------------

def test_point_identity():
    im = Image.new("L", (5, 5), 100)
    out = im.point(lambda x: x)
    assert out.getpixel((0, 0)) == 100


def test_point_double():
    im = Image.new("L", (5, 5), 50)
    out = im.point(lambda x: min(255, x * 2))
    assert out.getpixel((0, 0)) == 100


def test_point_invert():
    im = Image.new("L", (5, 5), 100)
    out = im.point(lambda x: 255 - x)
    assert out.getpixel((0, 0)) == 155


def test_point_zero():
    im = Image.new("L", (5, 5), 200)
    out = im.point(lambda x: 0)
    assert out.getpixel((0, 0)) == 0


def test_point_all_255():
    im = Image.new("L", (5, 5), 50)
    out = im.point(lambda x: 255)
    assert out.getpixel((0, 0)) == 255


def test_point_threshold():
    """Point as threshold: values >= 128 → 255, else 0."""
    im = Image.new("L", (3, 1), 0)
    im.putpixel((0, 0), 100)
    im.putpixel((1, 0), 128)
    im.putpixel((2, 0), 200)
    out = im.point(lambda x: 255 if x >= 128 else 0)
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((1, 0)) == 255
    assert out.getpixel((2, 0)) == 255


def test_point_clipping():
    """Values that map > 255 should be clamped."""
    im = Image.new("L", (5, 5), 200)
    out = im.point(lambda x: min(255, x * 3))
    assert out.getpixel((0, 0)) == 255


def test_point_returns_new_image():
    im = Image.new("L", (5, 5), 100)
    out = im.point(lambda x: x)
    assert out is not im


def test_point_preserves_mode_L():
    im = Image.new("L", (5, 5), 100)
    out = im.point(lambda x: x)
    assert out.mode == "L"


def test_point_preserves_size():
    im = Image.new("L", (20, 30), 100)
    out = im.point(lambda x: x)
    assert out.size == (20, 30)


# ---------------------------------------------------------------------------
# point() with a lookup table (256-element list)
# ---------------------------------------------------------------------------

def test_point_lut_identity():
    lut = list(range(256))
    im = Image.new("L", (5, 5), 100)
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 100


def test_point_lut_all_zero():
    lut = [0] * 256
    im = Image.new("L", (5, 5), 200)
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 0


def test_point_lut_all_255():
    lut = [255] * 256
    im = Image.new("L", (5, 5), 0)
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 255


def test_point_lut_invert():
    lut = [255 - i for i in range(256)]
    im = Image.new("L", (5, 5), 100)
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 155


def test_point_lut_specific_values():
    lut = [0] * 256
    lut[50] = 200
    lut[100] = 150
    im = Image.new("L", (2, 1), 0)
    im.putpixel((0, 0), 50)
    im.putpixel((1, 0), 100)
    out = im.point(lut)
    assert out.getpixel((0, 0)) == 200
    assert out.getpixel((1, 0)) == 150


# ---------------------------------------------------------------------------
# point() on RGB
# ---------------------------------------------------------------------------

def test_point_rgb_each_channel():
    """RGB point applies the function to each channel independently."""
    im = Image.new("RGB", (2, 1), (100, 150, 200))
    out = im.point(lambda x: 255 - x)
    r, g, b = out.getpixel((0, 0))
    assert r == 155
    assert g == 105
    assert b == 55


def test_point_rgb_preserves_mode():
    im = Image.new("RGB", (5, 5), (100, 100, 100))
    out = im.point(lambda x: x)
    assert out.mode == "RGB"


# ---------------------------------------------------------------------------
# point() does not modify original
# ---------------------------------------------------------------------------

def test_point_does_not_modify_original():
    im = Image.new("L", (5, 5), 100)
    out = im.point(lambda x: 255 - x)
    assert im.getpixel((0, 0)) == 100  # original unchanged


if __name__ == "__main__":
    pytest.main()
