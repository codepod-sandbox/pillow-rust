"""Tests for Image.convert() with mode arguments and optional matrix."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Basic mode conversions
# ---------------------------------------------------------------------------

def test_convert_RGB_to_L():
    im = Image.new("RGB", (4, 4), (100, 150, 200))
    out = im.convert("L")
    assert out.mode == "L"
    # BT.601 luma: (r*19595 + g*38470 + b*7471 + 0x8000) >> 16
    expected = (100 * 19595 + 150 * 38470 + 200 * 7471 + 0x8000) >> 16
    val = out.getpixel((0, 0))
    assert abs(int(val) - expected) <= 1


def test_convert_L_to_RGB():
    im = Image.new("L", (4, 4), 128)
    out = im.convert("RGB")
    assert out.mode == "RGB"
    r, g, b = out.getpixel((0, 0))
    assert r == 128
    assert g == 128
    assert b == 128


def test_convert_RGB_to_RGBA():
    im = Image.new("RGB", (4, 4), (10, 20, 30))
    out = im.convert("RGBA")
    assert out.mode == "RGBA"
    r, g, b, a = out.getpixel((0, 0))
    assert r == 10
    assert g == 20
    assert b == 30
    assert a == 255  # fully opaque


def test_convert_RGBA_to_RGB():
    im = Image.new("RGBA", (4, 4), (10, 20, 30, 128))
    out = im.convert("RGB")
    assert out.mode == "RGB"
    r, g, b = out.getpixel((0, 0))
    assert r == 10
    assert g == 20
    assert b == 30


def test_convert_L_to_1_threshold():
    """L to mode '1': values >= 128 → True (255), values < 128 → False (0)."""
    im = Image.new("L", (4, 1), 0)
    im.putpixel((0, 0), 0)
    im.putpixel((1, 0), 127)
    im.putpixel((2, 0), 128)
    im.putpixel((3, 0), 255)
    out = im.convert("1")
    assert out.mode == "1"
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((1, 0)) == 0
    assert out.getpixel((2, 0)) != 0
    assert out.getpixel((3, 0)) != 0


def test_convert_1_to_L():
    im = Image.new("1", (2, 1), 0)
    im.putpixel((1, 0), 255)
    out = im.convert("L")
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((1, 0)) == 255


def test_convert_RGB_to_1():
    im = Image.new("RGB", (2, 1), (0, 0, 0))
    im.putpixel((1, 0), (255, 255, 255))
    out = im.convert("1")
    assert out.mode == "1"
    assert out.getpixel((0, 0)) == 0
    assert out.getpixel((1, 0)) != 0


def test_convert_preserves_size():
    im = Image.new("RGB", (30, 20), (1, 2, 3))
    out = im.convert("L")
    assert out.size == (30, 20)


def test_convert_returns_new_image():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    out = im.convert("L")
    assert out is not im


# ---------------------------------------------------------------------------
# L to RGB and back roundtrip
# ---------------------------------------------------------------------------

def test_roundtrip_L_RGB_L():
    """L→RGB→L should recover the same value (via equal RGB channels)."""
    im = Image.new("L", (5, 5), 77)
    rgb = im.convert("RGB")
    back = rgb.convert("L")
    # Back to L via luma formula on equal channels: r==g==b==77 → 77
    val = back.getpixel((0, 0))
    assert abs(int(val) - 77) <= 1


def test_convert_LA_to_RGBA():
    im = Image.new("LA", (4, 4), (100, 200))
    out = im.convert("RGBA")
    assert out.mode == "RGBA"
    r, g, b, a = out.getpixel((0, 0))
    assert r == 100
    assert g == 100
    assert b == 100
    assert a == 200


def test_convert_RGBA_to_LA():
    im = Image.new("RGBA", (4, 4), (100, 100, 100, 200))
    out = im.convert("LA")
    assert out.mode == "LA"
    l_val, a = out.getpixel((0, 0))
    assert abs(l_val - 100) <= 1
    assert a == 200


def test_convert_same_mode_noop():
    """Converting to the same mode should return equivalent image."""
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    out = im.convert("RGB")
    assert out.mode == "RGB"
    assert out.getpixel((0, 0)) == (10, 20, 30)


# ---------------------------------------------------------------------------
# convert() with matrix (RGB→RGB color transform)
# ---------------------------------------------------------------------------

def test_convert_matrix_identity():
    """Identity matrix should leave RGB unchanged."""
    im = Image.new("RGB", (4, 4), (100, 150, 200))
    matrix = [1, 0, 0, 0,
               0, 1, 0, 0,
               0, 0, 1, 0]
    out = im.convert("RGB", matrix=matrix)
    assert out.mode == "RGB"
    r, g, b = out.getpixel((0, 0))
    assert abs(r - 100) <= 2
    assert abs(g - 150) <= 2
    assert abs(b - 200) <= 2


def test_convert_matrix_swap_rb():
    """Matrix that swaps R and B channels."""
    im = Image.new("RGB", (4, 4), (200, 100, 50))
    # B = R, G = G, R = B
    matrix = [0, 0, 1, 0,
               0, 1, 0, 0,
               1, 0, 0, 0]
    out = im.convert("RGB", matrix=matrix)
    r, g, b = out.getpixel((0, 0))
    assert abs(r - 50) <= 2   # was B
    assert abs(g - 100) <= 2  # unchanged
    assert abs(b - 200) <= 2  # was R


def test_convert_matrix_to_L():
    """Matrix can convert RGB to L."""
    im = Image.new("RGB", (4, 4), (255, 0, 0))
    # Luma formula via matrix: only R channel
    matrix = [0.299, 0.587, 0.114, 0]
    out = im.convert("L", matrix=matrix)
    assert out.mode == "L"
    # Should be close to R * 0.299 = 76
    val = out.getpixel((0, 0))
    assert 60 <= int(val) <= 90


if __name__ == "__main__":
    pytest.main()
