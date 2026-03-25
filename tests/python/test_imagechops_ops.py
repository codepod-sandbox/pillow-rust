"""Tests for ImageChops operations — exact pixel arithmetic."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageChops


def _L(size=(5, 5), val=0):
    return Image.new("L", size, val)


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

def test_add_basic():
    im1 = _L(val=100)
    im2 = _L(val=50)
    out = ImageChops.add(im1, im2)
    assert out.getpixel((0, 0)) == 150


def test_add_clamps_at_255():
    im1 = _L(val=200)
    im2 = _L(val=100)
    out = ImageChops.add(im1, im2)
    assert out.getpixel((0, 0)) == 255


def test_add_zero():
    im1 = _L(val=0)
    im2 = _L(val=0)
    out = ImageChops.add(im1, im2)
    assert out.getpixel((0, 0)) == 0


def test_add_with_scale():
    im1 = _L(val=100)
    im2 = _L(val=100)
    out = ImageChops.add(im1, im2, scale=2.0)
    # (100 + 100) / 2 = 100
    assert out.getpixel((0, 0)) == 100


# ---------------------------------------------------------------------------
# subtract
# ---------------------------------------------------------------------------

def test_subtract_basic():
    im1 = _L(val=150)
    im2 = _L(val=50)
    out = ImageChops.subtract(im1, im2)
    assert out.getpixel((0, 0)) == 100


def test_subtract_clamps_at_0():
    im1 = _L(val=50)
    im2 = _L(val=100)
    out = ImageChops.subtract(im1, im2)
    assert out.getpixel((0, 0)) == 0


def test_subtract_with_offset():
    im1 = _L(val=50)
    im2 = _L(val=100)
    out = ImageChops.subtract(im1, im2, offset=128)
    # (50 - 100) + 128 = 78
    assert out.getpixel((0, 0)) == 78


# ---------------------------------------------------------------------------
# multiply
# ---------------------------------------------------------------------------

def test_multiply_white_unchanged():
    """Multiplying by white (255) should keep the image unchanged."""
    im1 = _L(val=100)
    im2 = _L(val=255)
    out = ImageChops.multiply(im1, im2)
    # 100 * 255 / 255 = 100
    assert out.getpixel((0, 0)) == 100


def test_multiply_black_zeroes():
    """Multiplying by black (0) should return black."""
    im1 = _L(val=200)
    im2 = _L(val=0)
    out = ImageChops.multiply(im1, im2)
    assert out.getpixel((0, 0)) == 0


def test_multiply_half():
    """Multiplying by half (128) should roughly halve the value."""
    im1 = _L(val=200)
    im2 = _L(val=128)
    out = ImageChops.multiply(im1, im2)
    # 200 * 128 / 255 ≈ 100
    assert abs(out.getpixel((0, 0)) - 100) <= 5


# ---------------------------------------------------------------------------
# screen
# ---------------------------------------------------------------------------

def test_screen_two_blacks():
    """Screen of two black images → black."""
    im1 = _L(val=0)
    im2 = _L(val=0)
    out = ImageChops.screen(im1, im2)
    assert out.getpixel((0, 0)) == 0


def test_screen_one_white():
    """Screen with white → white."""
    im1 = _L(val=100)
    im2 = _L(val=255)
    out = ImageChops.screen(im1, im2)
    assert out.getpixel((0, 0)) == 255


def test_screen_both_50pct():
    """Screen of 128 with 128 is approximately 192."""
    im1 = _L(val=128)
    im2 = _L(val=128)
    out = ImageChops.screen(im1, im2)
    # screen = 255 - (255-a)*(255-b)/255 = 255 - 127*127/255 ≈ 192
    assert abs(out.getpixel((0, 0)) - 192) <= 5


# ---------------------------------------------------------------------------
# difference
# ---------------------------------------------------------------------------

def test_difference_same():
    im1 = _L(val=100)
    im2 = _L(val=100)
    out = ImageChops.difference(im1, im2)
    assert out.getpixel((0, 0)) == 0


def test_difference_basic():
    im1 = _L(val=200)
    im2 = _L(val=100)
    out = ImageChops.difference(im1, im2)
    assert out.getpixel((0, 0)) == 100


def test_difference_reversed():
    im1 = _L(val=100)
    im2 = _L(val=200)
    out = ImageChops.difference(im1, im2)
    assert out.getpixel((0, 0)) == 100  # abs(100 - 200)


# ---------------------------------------------------------------------------
# lighter / darker
# ---------------------------------------------------------------------------

def test_lighter_picks_brighter():
    im1 = _L(val=100)
    im2 = _L(val=200)
    out = ImageChops.lighter(im1, im2)
    assert out.getpixel((0, 0)) == 200


def test_lighter_same():
    im1 = _L(val=150)
    im2 = _L(val=150)
    out = ImageChops.lighter(im1, im2)
    assert out.getpixel((0, 0)) == 150


def test_darker_picks_darker():
    im1 = _L(val=100)
    im2 = _L(val=200)
    out = ImageChops.darker(im1, im2)
    assert out.getpixel((0, 0)) == 100


def test_darker_same():
    im1 = _L(val=150)
    im2 = _L(val=150)
    out = ImageChops.darker(im1, im2)
    assert out.getpixel((0, 0)) == 150


# ---------------------------------------------------------------------------
# invert
# ---------------------------------------------------------------------------

def test_invert_zero():
    im = _L(val=0)
    out = ImageChops.invert(im)
    assert out.getpixel((0, 0)) == 255


def test_invert_255():
    im = _L(val=255)
    out = ImageChops.invert(im)
    assert out.getpixel((0, 0)) == 0


def test_invert_100():
    im = _L(val=100)
    out = ImageChops.invert(im)
    assert out.getpixel((0, 0)) == 155


def test_invert_is_own_inverse():
    im = _L(val=150)
    out = ImageChops.invert(ImageChops.invert(im))
    assert out.getpixel((0, 0)) == 150


# ---------------------------------------------------------------------------
# offset
# ---------------------------------------------------------------------------

def test_offset_shifts_image():
    im = Image.new("L", (10, 10), 0)
    im.putpixel((0, 0), 200)
    out = ImageChops.offset(im, 2, 2)
    # Pixel that was at (0, 0) should now be at (2, 2)
    assert out.getpixel((2, 2)) == 200


def test_offset_zero():
    im = Image.new("L", (10, 10), 100)
    out = ImageChops.offset(im, 0, 0)
    assert out.getpixel((5, 5)) == 100


# ---------------------------------------------------------------------------
# Operations return new images
# ---------------------------------------------------------------------------

def test_add_returns_new():
    im1 = _L(val=100)
    im2 = _L(val=50)
    out = ImageChops.add(im1, im2)
    assert out is not im1
    assert out is not im2


def test_difference_returns_new():
    im1 = _L(val=100)
    im2 = _L(val=50)
    out = ImageChops.difference(im1, im2)
    assert out is not im1


if __name__ == "__main__":
    pytest.main()
