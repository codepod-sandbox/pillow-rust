"""Tests for Image.split() and Image.merge() — exact values."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# split()
# ---------------------------------------------------------------------------

def test_split_rgb_returns_three_bands():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    bands = im.split()
    assert len(bands) == 3


def test_split_rgb_band_modes():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    r, g, b = im.split()
    assert r.mode == "L"
    assert g.mode == "L"
    assert b.mode == "L"


def test_split_rgb_band_values():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    r, g, b = im.split()
    assert r.getpixel((0, 0)) == 10
    assert g.getpixel((0, 0)) == 20
    assert b.getpixel((0, 0)) == 30


def test_split_rgba_returns_four_bands():
    im = Image.new("RGBA", (5, 5), (10, 20, 30, 200))
    bands = im.split()
    assert len(bands) == 4


def test_split_rgba_band_values():
    im = Image.new("RGBA", (5, 5), (10, 20, 30, 200))
    r, g, b, a = im.split()
    assert r.getpixel((0, 0)) == 10
    assert g.getpixel((0, 0)) == 20
    assert b.getpixel((0, 0)) == 30
    assert a.getpixel((0, 0)) == 200


def test_split_L_returns_self():
    """Splitting an L image returns a tuple with one band."""
    im = Image.new("L", (5, 5), 128)
    bands = im.split()
    assert len(bands) == 1
    assert bands[0].mode == "L"
    assert bands[0].getpixel((0, 0)) == 128


def test_split_LA_returns_two_bands():
    im = Image.new("LA", (5, 5), (100, 200))
    bands = im.split()
    assert len(bands) == 2
    assert bands[0].getpixel((0, 0)) == 100  # L
    assert bands[1].getpixel((0, 0)) == 200  # A


def test_split_preserves_size():
    im = Image.new("RGB", (20, 30), (1, 2, 3))
    r, g, b = im.split()
    assert r.size == (20, 30)
    assert g.size == (20, 30)
    assert b.size == (20, 30)


def test_split_varying_pixels():
    """split() with non-uniform image."""
    im = Image.new("RGB", (2, 1), 0)
    im.putpixel((0, 0), (100, 150, 200))
    im.putpixel((1, 0), (50, 75, 100))
    r, g, b = im.split()
    assert r.getpixel((0, 0)) == 100
    assert r.getpixel((1, 0)) == 50
    assert g.getpixel((0, 0)) == 150
    assert b.getpixel((1, 0)) == 100


# ---------------------------------------------------------------------------
# merge()
# ---------------------------------------------------------------------------

def test_merge_rgb_from_bands():
    r = Image.new("L", (5, 5), 10)
    g = Image.new("L", (5, 5), 20)
    b = Image.new("L", (5, 5), 30)
    out = Image.merge("RGB", (r, g, b))
    assert out.mode == "RGB"
    assert out.getpixel((0, 0)) == (10, 20, 30)


def test_merge_rgba_from_bands():
    r = Image.new("L", (5, 5), 10)
    g = Image.new("L", (5, 5), 20)
    b = Image.new("L", (5, 5), 30)
    a = Image.new("L", (5, 5), 200)
    out = Image.merge("RGBA", (r, g, b, a))
    assert out.mode == "RGBA"
    assert out.getpixel((0, 0)) == (10, 20, 30, 200)


def test_merge_preserves_size():
    r = Image.new("L", (20, 30), 10)
    g = Image.new("L", (20, 30), 20)
    b = Image.new("L", (20, 30), 30)
    out = Image.merge("RGB", (r, g, b))
    assert out.size == (20, 30)


def test_split_merge_roundtrip():
    """split() then merge() recovers the original image."""
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    bands = im.split()
    out = Image.merge("RGB", bands)
    assert out.mode == "RGB"
    assert out.getpixel((0, 0)) == (100, 150, 200)


def test_split_merge_rgba_roundtrip():
    im = Image.new("RGBA", (5, 5), (10, 20, 30, 200))
    bands = im.split()
    out = Image.merge("RGBA", bands)
    assert out.getpixel((0, 0)) == (10, 20, 30, 200)


def test_merge_wrong_band_count_raises():
    r = Image.new("L", (5, 5), 0)
    g = Image.new("L", (5, 5), 0)
    with pytest.raises((ValueError, Exception)):
        Image.merge("RGB", (r, g))  # need 3 bands, gave 2


def test_merge_single_band_L():
    band = Image.new("L", (5, 5), 128)
    out = Image.merge("L", (band,))
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 128


def test_merge_reorder_channels():
    """Merge with reordered bands swaps the channels."""
    im = Image.new("RGB", (3, 1), 0)
    im.putpixel((0, 0), (100, 150, 200))
    im.putpixel((1, 0), (10, 20, 30))
    im.putpixel((2, 0), (50, 60, 70))
    r, g, b = im.split()
    # Swap R and B
    out = Image.merge("RGB", (b, g, r))
    assert out.getpixel((0, 0)) == (200, 150, 100)
    assert out.getpixel((1, 0)) == (30, 20, 10)


if __name__ == "__main__":
    pytest.main()
