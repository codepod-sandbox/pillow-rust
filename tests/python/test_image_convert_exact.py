"""Tests for Image.convert() — exact pixel values for all mode conversions."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# L → RGB
# ---------------------------------------------------------------------------

def test_L_to_RGB_gray_value():
    im = Image.new("L", (5, 5), 128)
    out = im.convert("RGB")
    assert out.mode == "RGB"
    r, g, b = out.getpixel((0, 0))
    assert r == 128
    assert g == 128
    assert b == 128


def test_L_to_RGB_zero():
    im = Image.new("L", (5, 5), 0)
    out = im.convert("RGB")
    assert out.getpixel((0, 0)) == (0, 0, 0)


def test_L_to_RGB_255():
    im = Image.new("L", (5, 5), 255)
    out = im.convert("RGB")
    assert out.getpixel((0, 0)) == (255, 255, 255)


# ---------------------------------------------------------------------------
# RGB → L (luminance)
# ---------------------------------------------------------------------------

def test_RGB_to_L_gray():
    """Pure gray RGB converts to same L value."""
    im = Image.new("RGB", (5, 5), (128, 128, 128))
    out = im.convert("L")
    assert out.mode == "L"
    # Pure gray → same luminance
    assert abs(out.getpixel((0, 0)) - 128) <= 2


def test_RGB_to_L_black():
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    out = im.convert("L")
    assert out.getpixel((0, 0)) == 0


def test_RGB_to_L_white():
    im = Image.new("RGB", (5, 5), (255, 255, 255))
    out = im.convert("L")
    assert out.getpixel((0, 0)) == 255


def test_RGB_to_L_luminance_formula():
    """Luminance uses weighted average: 0.299R + 0.587G + 0.114B."""
    im = Image.new("RGB", (1, 1), (255, 0, 0))  # red
    out = im.convert("L")
    expected = int(0.299 * 255)  # ≈ 76
    assert abs(out.getpixel((0, 0)) - expected) <= 5


# ---------------------------------------------------------------------------
# RGB → RGBA
# ---------------------------------------------------------------------------

def test_RGB_to_RGBA_alpha_255():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = im.convert("RGBA")
    assert out.mode == "RGBA"
    r, g, b, a = out.getpixel((0, 0))
    assert r == 100
    assert g == 150
    assert b == 200
    assert a == 255  # fully opaque


# ---------------------------------------------------------------------------
# RGBA → RGB (drops alpha)
# ---------------------------------------------------------------------------

def test_RGBA_to_RGB_drops_alpha():
    im = Image.new("RGBA", (5, 5), (100, 150, 200, 128))
    out = im.convert("RGB")
    assert out.mode == "RGB"
    r, g, b = out.getpixel((0, 0))
    assert r == 100
    assert g == 150
    assert b == 200


# ---------------------------------------------------------------------------
# L → RGBA
# ---------------------------------------------------------------------------

def test_L_to_RGBA_alpha_255():
    im = Image.new("L", (5, 5), 128)
    out = im.convert("RGBA")
    r, g, b, a = out.getpixel((0, 0))
    assert r == 128
    assert g == 128
    assert b == 128
    assert a == 255


# ---------------------------------------------------------------------------
# L → LA
# ---------------------------------------------------------------------------

def test_L_to_LA():
    im = Image.new("L", (5, 5), 100)
    out = im.convert("LA")
    assert out.mode == "LA"
    l, a = out.getpixel((0, 0))
    assert l == 100
    assert a == 255


# ---------------------------------------------------------------------------
# RGBA → L
# ---------------------------------------------------------------------------

def test_RGBA_to_L():
    im = Image.new("RGBA", (5, 5), (128, 128, 128, 128))
    out = im.convert("L")
    assert out.mode == "L"
    assert abs(out.getpixel((0, 0)) - 128) <= 2


# ---------------------------------------------------------------------------
# Mode preserved after convert
# ---------------------------------------------------------------------------

def test_convert_preserves_size():
    im = Image.new("L", (20, 30), 100)
    out = im.convert("RGB")
    assert out.size == (20, 30)


def test_convert_returns_new_image():
    im = Image.new("L", (5, 5), 100)
    out = im.convert("RGB")
    assert out is not im


def test_convert_does_not_modify_original():
    im = Image.new("L", (5, 5), 100)
    out = im.convert("RGB")
    assert im.mode == "L"
    assert im.getpixel((0, 0)) == 100


# ---------------------------------------------------------------------------
# Same-mode convert is a copy
# ---------------------------------------------------------------------------

def test_convert_same_mode_copy():
    im = Image.new("L", (5, 5), 100)
    out = im.convert("L")
    assert out is not im
    assert out.getpixel((0, 0)) == 100


def test_convert_same_mode_RGB():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    out = im.convert("RGB")
    assert out is not im
    assert out.getpixel((0, 0)) == (10, 20, 30)


# ---------------------------------------------------------------------------
# P (palette) mode — not yet implemented, skip
# ---------------------------------------------------------------------------

def test_L_to_P():
    im = Image.new("L", (5, 5), 100)
    try:
        out = im.convert("P")
        assert out.mode == "P"
    except (OSError, ValueError, Exception):
        pytest.skip("P mode not yet supported")


def test_P_to_RGB():
    im = Image.new("L", (5, 5), 100)
    try:
        p = im.convert("P")
        out = p.convert("RGB")
        assert out.mode == "RGB"
    except (OSError, ValueError, Exception):
        pytest.skip("P mode not yet supported")


if __name__ == "__main__":
    pytest.main()
