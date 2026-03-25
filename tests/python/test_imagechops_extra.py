"""Extended ImageChops tests — channel arithmetic, compositing."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image, ImageChops


def _solid(mode, color, size=(8, 8)):
    return Image.new(mode, size, color)


# ---------------------------------------------------------------------------
# add() — per-pixel addition
# ---------------------------------------------------------------------------

def test_add_clamp_at_255():
    """(200 + 100) / 1 = 300 → clamped to 255."""
    a = _solid("L", 200)
    b = _solid("L", 100)
    out = ImageChops.add(a, b)
    assert out.getpixel((0, 0)) == 255


def test_add_no_overflow_for_small_values():
    a = _solid("L", 50)
    b = _solid("L", 30)
    out = ImageChops.add(a, b)
    assert out.getpixel((0, 0)) == 80


def test_add_zero():
    a = _solid("L", 128)
    b = _solid("L", 0)
    out = ImageChops.add(a, b)
    assert out.getpixel((0, 0)) == 128


def test_add_rgb():
    a = _solid("RGB", (100, 50, 0))
    b = _solid("RGB", (100, 200, 255))
    out = ImageChops.add(a, b)
    r, g, b_ = out.getpixel((0, 0))
    assert r == 200
    assert g == 250
    assert b_ == 255


def test_add_with_scale():
    """(100 + 100) / 2 = 100."""
    a = _solid("L", 100)
    b = _solid("L", 100)
    out = ImageChops.add(a, b, scale=2.0)
    assert out.getpixel((0, 0)) == 100


# ---------------------------------------------------------------------------
# subtract() — per-pixel subtraction
# ---------------------------------------------------------------------------

def test_subtract_positive():
    """(200 - 100) / 1 + 0 = 100."""
    a = _solid("L", 200)
    b = _solid("L", 100)
    out = ImageChops.subtract(a, b)
    assert out.getpixel((0, 0)) == 100


def test_subtract_negative_clamp():
    """(50 - 100) / 1 + 0 = -50 → 0."""
    a = _solid("L", 50)
    b = _solid("L", 100)
    out = ImageChops.subtract(a, b)
    assert out.getpixel((0, 0)) == 0


def test_subtract_with_offset():
    """(100 - 200) / 1 + 128 = 28."""
    a = _solid("L", 100)
    b = _solid("L", 200)
    out = ImageChops.subtract(a, b, offset=128)
    assert out.getpixel((0, 0)) == 28


# ---------------------------------------------------------------------------
# multiply() — channel multiplication
# ---------------------------------------------------------------------------

def test_multiply_by_white():
    """Multiply by white (255) = identity."""
    a = _solid("L", 100)
    b = _solid("L", 255)
    out = ImageChops.multiply(a, b)
    assert out.getpixel((0, 0)) == 100


def test_multiply_by_black():
    """Multiply by black (0) = zero."""
    a = _solid("L", 200)
    b = _solid("L", 0)
    out = ImageChops.multiply(a, b)
    assert out.getpixel((0, 0)) == 0


def test_multiply_half():
    """128 * 128 / 255 ≈ 64."""
    a = _solid("L", 128)
    b = _solid("L", 128)
    out = ImageChops.multiply(a, b)
    val = out.getpixel((0, 0))
    assert 60 <= int(val) <= 68


def test_multiply_rgb():
    a = _solid("RGB", (200, 128, 50))
    b = _solid("RGB", (255, 255, 0))
    out = ImageChops.multiply(a, b)
    r, g, b_ = out.getpixel((0, 0))
    assert r == 200  # 200 * 255 / 255 = 200
    assert b_ == 0    # 50 * 0 / 255 = 0


# ---------------------------------------------------------------------------
# screen() — inverse multiply
# ---------------------------------------------------------------------------

def test_screen_by_white():
    """Screen with white → 255."""
    a = _solid("L", 100)
    b = _solid("L", 255)
    out = ImageChops.screen(a, b)
    assert out.getpixel((0, 0)) == 255


def test_screen_by_black():
    """Screen with black → identity."""
    a = _solid("L", 100)
    b = _solid("L", 0)
    out = ImageChops.screen(a, b)
    assert out.getpixel((0, 0)) == 100


# ---------------------------------------------------------------------------
# logical_and, logical_or, logical_xor
# ---------------------------------------------------------------------------

def test_logical_and_both_nonzero():
    a = _solid("L", 200)
    b = _solid("L", 100)
    out = ImageChops.logical_and(a, b)
    assert out.getpixel((0, 0)) == 255


def test_logical_and_one_zero():
    a = _solid("L", 200)
    b = _solid("L", 0)
    out = ImageChops.logical_and(a, b)
    assert out.getpixel((0, 0)) == 0


def test_logical_or_one_nonzero():
    a = _solid("L", 0)
    b = _solid("L", 100)
    out = ImageChops.logical_or(a, b)
    assert out.getpixel((0, 0)) == 255


def test_logical_or_both_zero():
    a = _solid("L", 0)
    b = _solid("L", 0)
    out = ImageChops.logical_or(a, b)
    assert out.getpixel((0, 0)) == 0


def test_logical_xor_same():
    a = _solid("L", 200)
    b = _solid("L", 100)
    out = ImageChops.logical_xor(a, b)
    assert out.getpixel((0, 0)) == 0  # both nonzero → 0


def test_logical_xor_different():
    a = _solid("L", 200)
    b = _solid("L", 0)
    out = ImageChops.logical_xor(a, b)
    assert out.getpixel((0, 0)) == 255  # one nonzero → 255


# ---------------------------------------------------------------------------
# difference()
# ---------------------------------------------------------------------------

def test_difference_symmetric():
    """difference(a, b) == difference(b, a)."""
    a = _solid("L", 100)
    b = _solid("L", 200)
    out1 = ImageChops.difference(a, b)
    out2 = ImageChops.difference(b, a)
    assert out1.getpixel((0, 0)) == out2.getpixel((0, 0)) == 100


def test_difference_self_is_zero():
    a = _solid("L", 150)
    out = ImageChops.difference(a, a)
    assert out.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# lighter / darker
# ---------------------------------------------------------------------------

def test_lighter_picks_max():
    a = _solid("L", 100)
    b = _solid("L", 200)
    out = ImageChops.lighter(a, b)
    assert out.getpixel((0, 0)) == 200


def test_darker_picks_min():
    a = _solid("L", 100)
    b = _solid("L", 200)
    out = ImageChops.darker(a, b)
    assert out.getpixel((0, 0)) == 100


# ---------------------------------------------------------------------------
# invert()
# ---------------------------------------------------------------------------

def test_invert_255():
    a = _solid("L", 100)
    out = ImageChops.invert(a)
    assert out.getpixel((0, 0)) == 155


def test_invert_double_is_identity():
    a = _solid("L", 100)
    out = ImageChops.invert(ImageChops.invert(a))
    assert out.getpixel((0, 0)) == 100


if __name__ == "__main__":
    pytest.main()
