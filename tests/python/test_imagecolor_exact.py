"""Tests for ImageColor — exact color parsing and conversion."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import ImageColor


# ---------------------------------------------------------------------------
# getrgb() — parse color strings
# ---------------------------------------------------------------------------

def test_getrgb_black_name():
    assert ImageColor.getrgb("black") == (0, 0, 0)


def test_getrgb_white_name():
    assert ImageColor.getrgb("white") == (255, 255, 255)


def test_getrgb_red_name():
    r, g, b = ImageColor.getrgb("red")
    assert r == 255
    assert g == 0
    assert b == 0


def test_getrgb_green_name():
    r, g, b = ImageColor.getrgb("green")
    assert r == 0
    assert g > 0  # green is (0, 128, 0) or (0, 255, 0) depending on definition


def test_getrgb_blue_name():
    r, g, b = ImageColor.getrgb("blue")
    assert r == 0
    assert g == 0
    assert b == 255


def test_getrgb_hex_6():
    assert ImageColor.getrgb("#ff0000") == (255, 0, 0)


def test_getrgb_hex_6_blue():
    assert ImageColor.getrgb("#0000ff") == (0, 0, 255)


def test_getrgb_hex_6_mixed():
    r, g, b = ImageColor.getrgb("#1a2b3c")
    assert r == 0x1a
    assert g == 0x2b
    assert b == 0x3c


def test_getrgb_hex_3():
    """3-digit hex: #rgb → #rrggbb."""
    assert ImageColor.getrgb("#f00") == (255, 0, 0)


def test_getrgb_hex_3_white():
    assert ImageColor.getrgb("#fff") == (255, 255, 255)


def test_getrgb_hex_3_black():
    assert ImageColor.getrgb("#000") == (0, 0, 0)


def test_getrgb_rgb_function():
    assert ImageColor.getrgb("rgb(100, 150, 200)") == (100, 150, 200)


def test_getrgb_rgb_zeros():
    assert ImageColor.getrgb("rgb(0, 0, 0)") == (0, 0, 0)


def test_getrgb_rgb_255():
    assert ImageColor.getrgb("rgb(255, 255, 255)") == (255, 255, 255)


def test_getrgb_hsl():
    """hsl(0, 100%, 50%) = pure red."""
    r, g, b = ImageColor.getrgb("hsl(0, 100%, 50%)")
    assert r == 255
    assert g == 0
    assert b == 0


def test_getrgb_hsl_green():
    """hsl(120, 100%, 50%) = pure green."""
    r, g, b = ImageColor.getrgb("hsl(120, 100%, 50%)")
    assert r == 0
    assert g == 255
    assert b == 0


def test_getrgb_hsl_blue():
    """hsl(240, 100%, 50%) = pure blue."""
    r, g, b = ImageColor.getrgb("hsl(240, 100%, 50%)")
    assert r == 0
    assert g == 0
    assert b == 255


def test_getrgb_hsl_white():
    """hsl(0, 0%, 100%) = white."""
    r, g, b = ImageColor.getrgb("hsl(0, 0%, 100%)")
    assert r == 255
    assert g == 255
    assert b == 255


def test_getrgb_hsl_black():
    """hsl(0, 0%, 0%) = black."""
    r, g, b = ImageColor.getrgb("hsl(0, 0%, 0%)")
    assert r == 0
    assert g == 0
    assert b == 0


def test_getrgb_yellow():
    r, g, b = ImageColor.getrgb("yellow")
    assert r == 255
    assert g == 255
    assert b == 0


def test_getrgb_cyan():
    r, g, b = ImageColor.getrgb("cyan")
    assert r == 0
    assert g == 255
    assert b == 255


def test_getrgb_magenta():
    r, g, b = ImageColor.getrgb("magenta")
    assert r == 255
    assert g == 0
    assert b == 255


# ---------------------------------------------------------------------------
# getcolor() — returns value for given mode
# ---------------------------------------------------------------------------

def test_getcolor_L_red():
    """getcolor red in L mode → luminance of red."""
    v = ImageColor.getcolor("red", "L")
    assert isinstance(v, int)
    # Red has R=255, G=0, B=0 → luminance ≈ 76
    assert v > 50


def test_getcolor_L_white():
    v = ImageColor.getcolor("white", "L")
    assert v == 255


def test_getcolor_L_black():
    v = ImageColor.getcolor("black", "L")
    assert v == 0


def test_getcolor_RGB_red():
    v = ImageColor.getcolor("red", "RGB")
    assert v == (255, 0, 0)


def test_getcolor_RGBA_red():
    v = ImageColor.getcolor("red", "RGBA")
    r, g, b, a = v
    assert r == 255
    assert g == 0
    assert b == 0
    assert a == 255  # fully opaque


def test_getcolor_returns_tuple_for_RGB():
    v = ImageColor.getcolor("blue", "RGB")
    assert isinstance(v, tuple)


def test_getcolor_returns_int_for_L():
    v = ImageColor.getcolor("white", "L")
    assert isinstance(v, int)


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------

def test_getrgb_case_insensitive():
    assert ImageColor.getrgb("RED") == ImageColor.getrgb("red")
    assert ImageColor.getrgb("White") == ImageColor.getrgb("white")


if __name__ == "__main__":
    pytest.main()
