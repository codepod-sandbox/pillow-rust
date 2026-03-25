"""Tests for Image.split() and Image.merge() — exact pixel values."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# split()
# ---------------------------------------------------------------------------

def test_split_L_returns_single_band():
    im = Image.new("L", (5, 5), 128)
    bands = im.split()
    assert len(bands) == 1
    assert bands[0].mode == "L"
    assert bands[0].getpixel((0, 0)) == 128


def test_split_RGB_returns_3_bands():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    bands = im.split()
    assert len(bands) == 3


def test_split_RGB_band_values():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    r, g, b = im.split()
    assert r.getpixel((0, 0)) == 100
    assert g.getpixel((0, 0)) == 150
    assert b.getpixel((0, 0)) == 200


def test_split_RGBA_returns_4_bands():
    im = Image.new("RGBA", (5, 5), (100, 150, 200, 128))
    bands = im.split()
    assert len(bands) == 4


def test_split_RGBA_band_values():
    im = Image.new("RGBA", (5, 5), (100, 150, 200, 128))
    r, g, b, a = im.split()
    assert r.getpixel((0, 0)) == 100
    assert g.getpixel((0, 0)) == 150
    assert b.getpixel((0, 0)) == 200
    assert a.getpixel((0, 0)) == 128


def test_split_all_bands_are_L():
    im = Image.new("RGB", (5, 5), (10, 20, 30))
    for band in im.split():
        assert band.mode == "L"


def test_split_bands_have_correct_size():
    im = Image.new("RGB", (20, 30), (0, 0, 0))
    for band in im.split():
        assert band.size == (20, 30)


def test_split_LA():
    im = Image.new("LA", (5, 5), (100, 200))
    l, a = im.split()
    assert l.getpixel((0, 0)) == 100
    assert a.getpixel((0, 0)) == 200


def test_split_does_not_modify_original():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    bands = im.split()
    assert im.getpixel((0, 0)) == (100, 150, 200)


# ---------------------------------------------------------------------------
# merge()
# ---------------------------------------------------------------------------

def test_merge_RGB_from_L_bands():
    r = Image.new("L", (5, 5), 100)
    g = Image.new("L", (5, 5), 150)
    b = Image.new("L", (5, 5), 200)
    out = Image.merge("RGB", (r, g, b))
    assert out.mode == "RGB"
    assert out.getpixel((0, 0)) == (100, 150, 200)


def test_merge_RGBA_from_L_bands():
    r = Image.new("L", (5, 5), 100)
    g = Image.new("L", (5, 5), 150)
    b = Image.new("L", (5, 5), 200)
    a = Image.new("L", (5, 5), 128)
    out = Image.merge("RGBA", (r, g, b, a))
    v = out.getpixel((0, 0))
    assert v[0] == 100
    assert v[1] == 150
    assert v[2] == 200
    assert v[3] == 128


def test_merge_roundtrip():
    """split() then merge() should reconstruct original image."""
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    bands = im.split()
    out = Image.merge("RGB", bands)
    assert out.getpixel((0, 0)) == (100, 150, 200)


def test_merge_L_from_single():
    band = Image.new("L", (5, 5), 128)
    out = Image.merge("L", (band,))
    assert out.mode == "L"
    assert out.getpixel((0, 0)) == 128


def test_merge_preserves_size():
    r = Image.new("L", (20, 30), 100)
    g = Image.new("L", (20, 30), 150)
    b = Image.new("L", (20, 30), 200)
    out = Image.merge("RGB", (r, g, b))
    assert out.size == (20, 30)


def test_merge_varying_pixels():
    """Test merge with varying pixel values."""
    r = Image.new("L", (2, 1), 0)
    r.putpixel((0, 0), 50)
    r.putpixel((1, 0), 100)
    g = Image.new("L", (2, 1), 0)
    g.putpixel((0, 0), 150)
    g.putpixel((1, 0), 200)
    b = Image.new("L", (2, 1), 0)
    b.putpixel((0, 0), 250)
    b.putpixel((1, 0), 50)
    out = Image.merge("RGB", (r, g, b))
    assert out.getpixel((0, 0)) == (50, 150, 250)
    assert out.getpixel((1, 0)) == (100, 200, 50)


# ---------------------------------------------------------------------------
# getbands()
# ---------------------------------------------------------------------------

def test_getbands_L():
    im = Image.new("L", (5, 5), 0)
    assert im.getbands() == ("L",)


def test_getbands_RGB():
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    assert im.getbands() == ("R", "G", "B")


def test_getbands_RGBA():
    im = Image.new("RGBA", (5, 5), (0, 0, 0, 0))
    assert im.getbands() == ("R", "G", "B", "A")


def test_getbands_LA():
    im = Image.new("LA", (5, 5), (0, 0))
    assert im.getbands() == ("L", "A")


if __name__ == "__main__":
    pytest.main()
