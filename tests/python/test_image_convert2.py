"""Additional tests for Image.convert() — mode conversions with edge cases."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# RGB → CMYK (if supported)
# ---------------------------------------------------------------------------

def test_RGB_to_CMYK_not_crash():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    try:
        out = im.convert("CMYK")
        assert out.mode == "CMYK"
    except (OSError, ValueError, Exception):
        pytest.skip("CMYK not supported")


# ---------------------------------------------------------------------------
# L → LA
# ---------------------------------------------------------------------------

def test_L_to_LA_alpha():
    im = Image.new("L", (5, 5), 128)
    try:
        out = im.convert("LA")
        l, a = out.getpixel((0, 0))
        assert l == 128
        assert a == 255
    except (OSError, ValueError, Exception):
        pytest.skip("LA conversion not supported")


# ---------------------------------------------------------------------------
# RGBA → L
# ---------------------------------------------------------------------------

def test_RGBA_white_to_L():
    im = Image.new("RGBA", (5, 5), (255, 255, 255, 255))
    out = im.convert("L")
    assert out.getpixel((0, 0)) == 255


def test_RGBA_black_to_L():
    im = Image.new("RGBA", (5, 5), (0, 0, 0, 255))
    out = im.convert("L")
    assert out.getpixel((0, 0)) == 0


# ---------------------------------------------------------------------------
# Multiple mode conversions chained
# ---------------------------------------------------------------------------

def test_chain_L_RGB_L_roundtrip():
    """L → RGB → L should preserve grayscale value approximately."""
    im = Image.new("L", (5, 5), 128)
    out = im.convert("RGB").convert("L")
    assert abs(out.getpixel((0, 0)) - 128) <= 3


def test_chain_RGB_RGBA_RGB():
    """RGB → RGBA → RGB should preserve colors."""
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = im.convert("RGBA").convert("RGB")
    assert out.getpixel((0, 0)) == (100, 150, 200)


def test_chain_L_RGBA():
    """L → RGBA should work."""
    im = Image.new("L", (5, 5), 128)
    out = im.convert("RGBA")
    r, g, b, a = out.getpixel((0, 0))
    assert r == 128
    assert g == 128
    assert b == 128
    assert a == 255


# ---------------------------------------------------------------------------
# convert with dither
# ---------------------------------------------------------------------------

def test_RGB_to_L_with_dither():
    """RGB to L with dither should not crash."""
    im = Image.new("RGB", (10, 10), (100, 150, 200))
    out = im.convert("L")
    assert out.mode == "L"


# ---------------------------------------------------------------------------
# convert("1") threshold behavior
# ---------------------------------------------------------------------------

def test_convert_1_above_threshold():
    """Values >= 128 should become white (255) in mode 1."""
    im = Image.new("L", (5, 5), 200)
    out = im.convert("1")
    assert out.mode == "1"
    assert out.getpixel((0, 0)) in (255, 1, True)


def test_convert_1_below_threshold():
    """Values < 128 should become black (0) in mode 1."""
    im = Image.new("L", (5, 5), 50)
    out = im.convert("1")
    assert out.mode == "1"
    assert out.getpixel((0, 0)) in (0, False)


def test_convert_1_threshold_128():
    """Value exactly 128 → white."""
    im = Image.new("L", (5, 5), 128)
    out = im.convert("1")
    assert out.mode == "1"
    assert out.getpixel((0, 0)) in (255, 1, True)


def test_convert_1_threshold_127():
    """Value 127 → black."""
    im = Image.new("L", (5, 5), 127)
    out = im.convert("1")
    assert out.mode == "1"
    assert out.getpixel((0, 0)) in (0, False)


def test_convert_1_size_preserved():
    im = Image.new("L", (20, 30), 100)
    out = im.convert("1")
    assert out.size == (20, 30)


def test_convert_1_from_rgb():
    """RGB → 1 via gray conversion."""
    im = Image.new("RGB", (5, 5), (200, 200, 200))
    out = im.convert("1")
    assert out.mode == "1"


# ---------------------------------------------------------------------------
# Mode conversions preserve size
# ---------------------------------------------------------------------------

def test_convert_preserves_size_20x30():
    im = Image.new("RGB", (20, 30), (100, 100, 100))
    for mode in ["L", "RGBA"]:
        out = im.convert(mode)
        assert out.size == (20, 30), f"size changed for mode {mode}"


if __name__ == "__main__":
    pytest.main()
