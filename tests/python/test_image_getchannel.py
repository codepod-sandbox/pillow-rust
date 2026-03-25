"""Tests for Image.getchannel() — extract single band from multi-channel image."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# getchannel() by name
# ---------------------------------------------------------------------------

def test_getchannel_R_from_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    r = im.getchannel("R")
    assert r.mode == "L"
    assert r.getpixel((0, 0)) == 100


def test_getchannel_G_from_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    g = im.getchannel("G")
    assert g.mode == "L"
    assert g.getpixel((0, 0)) == 150


def test_getchannel_B_from_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    b = im.getchannel("B")
    assert b.mode == "L"
    assert b.getpixel((0, 0)) == 200


def test_getchannel_A_from_RGBA():
    im = Image.new("RGBA", (5, 5), (100, 150, 200, 128))
    a = im.getchannel("A")
    assert a.mode == "L"
    assert a.getpixel((0, 0)) == 128


def test_getchannel_A_from_LA():
    im = Image.new("LA", (5, 5), (100, 200))
    a = im.getchannel("A")
    assert a.mode == "L"
    assert a.getpixel((0, 0)) == 200


def test_getchannel_L_from_L():
    im = Image.new("L", (5, 5), 128)
    l_band = im.getchannel("L")
    assert l_band.mode == "L"
    assert l_band.getpixel((0, 0)) == 128


# ---------------------------------------------------------------------------
# getchannel() by index
# ---------------------------------------------------------------------------

def test_getchannel_index_0_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    r = im.getchannel(0)
    assert r.getpixel((0, 0)) == 100


def test_getchannel_index_1_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    g = im.getchannel(1)
    assert g.getpixel((0, 0)) == 150


def test_getchannel_index_2_RGB():
    im = Image.new("RGB", (5, 5), (100, 150, 200))
    b = im.getchannel(2)
    assert b.getpixel((0, 0)) == 200


def test_getchannel_index_3_RGBA():
    im = Image.new("RGBA", (5, 5), (100, 150, 200, 50))
    a = im.getchannel(3)
    assert a.getpixel((0, 0)) == 50


def test_getchannel_index_0_LA():
    im = Image.new("LA", (5, 5), (128, 200))
    l_band = im.getchannel(0)
    assert l_band.getpixel((0, 0)) == 128


# ---------------------------------------------------------------------------
# getchannel() preserves size
# ---------------------------------------------------------------------------

def test_getchannel_preserves_size():
    im = Image.new("RGB", (30, 20), (1, 2, 3))
    r = im.getchannel("R")
    assert r.size == (30, 20)


# ---------------------------------------------------------------------------
# getchannel() with varying pixels
# ---------------------------------------------------------------------------

def test_getchannel_varying_R():
    im = Image.new("RGB", (2, 1), (0, 0, 0))
    im.putpixel((0, 0), (100, 150, 200))
    im.putpixel((1, 0), (50, 75, 100))
    r = im.getchannel("R")
    assert r.getpixel((0, 0)) == 100
    assert r.getpixel((1, 0)) == 50


def test_getchannel_varying_A():
    im = Image.new("RGBA", (3, 1), (0, 0, 0, 0))
    im.putpixel((0, 0), (10, 20, 30, 50))
    im.putpixel((1, 0), (10, 20, 30, 150))
    im.putpixel((2, 0), (10, 20, 30, 255))
    a = im.getchannel("A")
    assert a.getpixel((0, 0)) == 50
    assert a.getpixel((1, 0)) == 150
    assert a.getpixel((2, 0)) == 255


# ---------------------------------------------------------------------------
# getchannel() error cases
# ---------------------------------------------------------------------------

def test_getchannel_invalid_name_raises():
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    with pytest.raises((ValueError, AttributeError, Exception)):
        im.getchannel("Z")


def test_getchannel_invalid_index_raises():
    im = Image.new("RGB", (5, 5), (0, 0, 0))
    with pytest.raises((ValueError, IndexError, Exception)):
        im.getchannel(10)


if __name__ == "__main__":
    pytest.main()
